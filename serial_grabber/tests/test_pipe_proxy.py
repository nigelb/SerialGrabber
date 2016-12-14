import unittest

from multiprocessing import Pipe

from serial_grabber.pipe_proxy import expose_object, PipeProxy, RemoteException


class TestClass:

    def true(self):
        return True

    def false(self):
        return False

    def exception(self):
        raise Exception()


class MyTestCase(unittest.TestCase):

    def test_true(self):
        left, right = Pipe()
        expose_object(left, TestClass())
        test = PipeProxy(right)
        self.assertEqual(test.false(), False)
        test.__close__()

    def test_exception(self):
        left, right = Pipe()
        expose_object(left, TestClass())
        test = PipeProxy(right)
        try:
            test.exception()
        except RemoteException as re:
            self.assertTrue(re)
        test.__close__()

    def test_unknown_method(self):

        left, right = Pipe()
        expose_object(left, TestClass())
        test = PipeProxy(right)
        try:
            print test.not_a_method()
        except RemoteException as re:
            self.assertTrue(type(re.exception) == AttributeError)
        test.__close__()


if __name__ == '__main__':
    unittest.main()
