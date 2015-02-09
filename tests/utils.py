from functools import wraps
from six import text_type


def skip_if_arguments_are_unicode(test_method):
    @wraps(test_method)
    def new_method(self, *args, **kwargs):
        subsequence, sequence = args[:2]
        if (
            isinstance(subsequence, text_type) or
            isinstance(sequence, text_type)
        ):
            raise self.skipTest(
                "skipping test with unicode data for byteslike function")

        return test_method(self, *args, **kwargs)

    return new_method
