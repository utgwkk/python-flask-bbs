import unittest
from main import generate_trip


class HelpersTest(unittest.TestCase):
    def test_generate_trip_short(self):
        self.assertEqual('◆/WG5qp963c', generate_trip('#istrip'))
        self.assertEqual('◆Ig9vRBfuyA', generate_trip('#Wikipedia'))
        self.assertEqual('◆////SPxx9k', generate_trip('#nMQ6cIO}'))

    def test_generate_trip_multibyte(self):
        self.assertEqual('◆pA8Bpf.Qvk', generate_trip('#ニコニコ'))


if __name__ == '__main__':
    unittest.main()
