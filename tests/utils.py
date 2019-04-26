from functools import wraps

from fuzzysearch.compat import text_type


def skip_if_arguments_arent_byteslike(test_method):
    @wraps(test_method)
    def new_method(self, *args, **kwargs):
        subsequence, sequence = args[:2]
        if (
            isinstance(subsequence, text_type) or
            isinstance(sequence, text_type)
        ):
            raise self.skipTest(
                "skipping test with unicode data for byteslike function")
        elif (
            isinstance(subsequence, (list, tuple)) or
            isinstance(sequence, (list, tuple))
        ):
            raise self.skipTest(
                "skipping test with list/tuple data for byteslike function")

        return test_method(self, *args, **kwargs)

    return new_method
