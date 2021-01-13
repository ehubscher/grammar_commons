import grammar_commons.lang_utils as lang_utils
import grammar_commons.string_utils as string_utils
import logging
import regex
from regex.regex import Match, Pattern
from typing import Dict, List, Set, Tuple

GROUPS_REGEX: str = r'(?P<atomic_groups>\((?:{language_regex}*|({language_regex}*\|{language_regex}*)*|({language_regex}*\|{language_regex}*\|{language_regex}*)*)\))'
OPTIONALS_REGEX: str = r'(?P<atomic_optionals>\[(?:{language_regex}*|({language_regex}*\|{language_regex}*)*|({language_regex}*\|{language_regex}*\|{language_regex}*)*)\])'
OPTIONS_REGEX: str = r'(?P<atomic_options>(?:{language_regex}*|({language_regex}*\|{language_regex}*)*|({language_regex}*\|{language_regex}*\|{language_regex}*)*))'
WORDS_REGEX: str = r'(?P<atomic_words>{language_regex}+)'

def get_potential_options(bnf: str, matched_value: str) -> Set[str]:
    """
    Takes a given BNF and a matched value for either an
    "atomic group" or "atomic optional" (see the docs for expand_bnf_recursive()).

    The matched value is stripped of brackets and/or parentheses and then split
    into it's corresponding options (if there are any).

    Then, each instance of the original matched value is replaced with either
    itself (minus the brackets/parentheses) or each and every one of the
    options contained within it (if there are any).

    :param bnf: BNF string operating on.
    :param matched_value: Value string of corresponding atomic group/optional.
    :return: List of BNF with all corresponding options/optional/group
    """

    expansions: Set[str] = set()
    matched_options: List[str] = split_options(matched_value)

    for option in matched_options:
        new_expansion: str = bnf.replace(matched_value, option, 1)
        expansions.add(new_expansion)

    return expansions


def are_all_words_only(sentences: Set[str], language_code: str) -> bool:
    """
    Determines whether a list of strings contains strings that have word
    characters only.
    """

    for sentence in sentences:
        if not is_words_only(sentence, language_code.lower()):
            return False

    return True


def expand_bnf_recursive(to_be_expanded: Set[str], language_code: str) -> List[str]:
    """
    Performs a recursive, bottom-up expansion on a BNF rule.

    Firstly, all BNFs in the to_be_expanded set are searched for an "atomic
    group" (i.e. in the form of "(one word or many words)" or "(some words | or | other words)")
    and proceeds to replace each atomic group in each corresponding BNF itself
    or each option within the group (if there are any).

    Secondly, after expanding by atomic groups, the resulting list of BNF
    expansions are iterated over and searched for an "atomic optional"
    (i.e. in the form of "[one word or many words]" or "[some words | or | other words]")
    which is then replaced with nothing, itself, and/or each option within the
    optional (if there are any).

    Lastly, if the resulting list of expansions contains strings of words only
    (i.e. proper sentences), then that is what will be returned.
    Otherwise, a recursive call is made with the result as the to_be_expanded
    parameter which will continue to grow with each recursive call.

    :param to_be_expanded: Un-finished expanded sentences of the original BNF rule.
    :param language_code: The specified language the BNFs are to be expanded in.
    :return: The sorted list of every expansion of the given BNF rule.
    """

    global GROUPS_REGEX
    global OPTIONALS_REGEX
    global OPTIONS_REGEX
    global WORDS_REGEX

    if language_code.lower() not in lang_utils.LANGUAGE_UNICODE_ALPHABET:
        logging.error('Language code provided is not supported.')
        return list()

    if not to_be_expanded:
        logging.error('No BNF(s) provided to expand.')
        return list()

    GROUPS_REGEX_FORMATTED: str = GROUPS_REGEX.format(language_regex=lang_utils.LANGUAGE_UNICODE_ALPHABET[language_code.lower()])
    OPTIONALS_REGEX_FORMATTED: str = OPTIONALS_REGEX.format(language_regex=lang_utils.LANGUAGE_UNICODE_ALPHABET[language_code.lower()])
    OPTIONS_REGEX_FORMATTED: str = OPTIONS_REGEX.format(language_regex=lang_utils.LANGUAGE_UNICODE_ALPHABET[language_code.lower()])

    GROUPS_PATTERN: Pattern = regex.compile(GROUPS_REGEX_FORMATTED)
    OPTIONALS_PATTERN: Pattern = regex.compile(OPTIONALS_REGEX_FORMATTED)
    OPTIONS_PATTERN: Pattern = regex.compile(OPTIONS_REGEX_FORMATTED)

    group_expansions: Set[str] = set()
    group_optional_expansions: Set[str] = set()
    option_expansions: Set[str] = set()

    for expanding in to_be_expanded:
        option_match: Match = OPTIONS_PATTERN.fullmatch(expanding)

        if not option_match or option_match.group('atomic_options') is str():
            option_expansions.add(expanding)
            continue

        options: str = option_match.group('atomic_options')
        option_expansions = option_expansions.union(split_options(options))

    for expanding in option_expansions:
        if validate_bnf_groups(expanding):
            group_match: Match = GROUPS_PATTERN.search(expanding)

            if not group_match or group_match.group('atomic_groups') is str():
                group_expansions.add(expanding)
                continue

            group: str = group_match.group('atomic_groups')
            group_expansions = group_expansions.union(get_potential_options(bnf=expanding, matched_value=group))
        else:
            return list()

    for expanding in group_expansions:
        optional_match: Match = OPTIONALS_PATTERN.search(expanding)

        if not optional_match or optional_match.group('atomic_optionals') is str():
            group_optional_expansions.add(expanding)
            continue

        optional: str = optional_match.group('atomic_optionals')

        tmp_new_expansion: str = expanding.replace(optional, str(), 1)
        group_optional_expansions.add(tmp_new_expansion.replace('  ', ' '))
        group_optional_expansions = group_optional_expansions.union(
            get_potential_options(bnf=expanding, matched_value=optional)
        )

    option_expansions = None
    group_expansions = None

    if not are_all_words_only(group_optional_expansions, language_code.lower()):
        return expand_bnf_recursive(group_optional_expansions, language_code)

    return sorted(group_optional_expansions)


def is_words_only(string: str, language_code: str) -> bool:
    """Determines whether a string for a given language contains word characters only."""

    global WORDS_REGEX

    if language_code.lower() not in lang_utils.LANGUAGE_UNICODE_ALPHABET:
        logging.error('Language code provided is not supported.')
        return False

    WORDS_REGEX_FORMATTED: str = WORDS_REGEX.format(language_regex=lang_utils.LANGUAGE_UNICODE_ALPHABET[language_code.lower()])
    WORDS_PATTERN: Pattern = regex.compile(WORDS_REGEX_FORMATTED)

    words_match: Match = regex.search(WORDS_PATTERN, string)

    return words_match.group('atomic_words') == string


def split_options(string: str) -> List[str]:
    """
    Returns set of unique words within a pipe-separated string
    (i.e. option group in a BNF.)
    """

    cleaned_string: str = string_utils.remove_from_string(
        string=string,
        symbols_to_remove=['(', ')', '[', ']']
    )

    return [value.strip() for value in cleaned_string.split('|')]


def validate_bnf_groups(bnf: str) -> bool:
    """Validates if a given BNF has all of it's groups/optionals appropriately closed/matched."""

    character_index = 0
    group_stack: List[Tuple[str, int]] = list()
    opening: Dict[str, str] = {'group': '(', 'optional': '['}
    closing: Dict[str, str] = {'group': ')', 'optional': ']'}

    for char in bnf:
        if char is opening['group'] or char is opening['optional']:
            group_stack.append((char, character_index))
            character_index += 1
            continue

        if char is closing['group']:
            if not group_stack:
                logging.warning(
                    f'The BNF \'{bnf}\' has a closing \'{closing["group"]} \' as a group opener at the '
                    f'{character_index}{string_utils.number_position_suffix(character_index)} character. '
                    f'\'{closing["group"]}\' must be preceded with \'{opening["group"]}\'.'
                )
                return False

            if group_stack[-1][0] is opening['group']:
                group_stack.pop()
                character_index += 1
                continue

            if group_stack[-1][0] is opening['optional']:
                logging.warning(
                    f'The BNF \'{bnf}\' has a mismatch at the {character_index}'
                    f'{string_utils.number_position_suffix(character_index)} character. '
                    f'Expected closing for \'{group_stack[-1][0]}\', received \'{closing["group"]}\'.'
                )
                return False

        if char is closing['optional']:
            if not group_stack:
                logging.warning(
                    f'The BNF \'{bnf}\' has a closing \'{closing["optional"]}\' as an optional opener at the '
                    f'{character_index}{string_utils.number_position_suffix(character_index)} character. '
                    f'\'{closing["optional"]}\' must be preceded with \'{opening["optional"]}\'.'
                )
                return False

            if group_stack[-1][0] is opening['optional']:
                group_stack.pop()
                character_index += 1
                continue

            if group_stack[-1][0] is opening['group']:
                logging.warning(
                    f'The BNF \'{bnf}\' has a mismatch at the {character_index}'
                    f'{string_utils.number_position_suffix(character_index)} character. '
                    f'Expected closing for \'{group_stack[-1][0]}\', received \'{closing["optional"]}\'.'
                )
                return False

        character_index += 1

    if not group_stack:
        return True

    for group, index in group_stack:
        if group is opening['group']:
            logging.warning(
                f'Missing closing \'{closing["group"]}\' for \'{group}\' located at the '
                f'{index}{string_utils.number_position_suffix(index)} character.'
            )

        if group is opening['optional']:
            logging.warning(
                f'Missing closing \'{closing["optional"]}\' for \'{group}\' located at the '
                f'{index}{string_utils.number_position_suffix(index)} character.'
            )

    return False


if __name__ == "__main__":
    import time

    start = time.perf_counter_ns()

    result: list = expand_bnf_recursive(
        {'(indicazioni per | (portami | guidami | vai) (a | verso)) ([un] indirizzo | via) a <city>'},
        'iti'
    )

    end = time.perf_counter_ns()

    print('\r\n'.join(result))
    print(f'{(end - start) / 1000000000} seconds')
