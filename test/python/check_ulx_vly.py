import unittest
import numpy
import irbasis as ir
import math


class TestMethods(unittest.TestCase):
    def __init__(self, *args, **kwargs):

        super(TestMethods, self).__init__(*args, **kwargs)

    def test_small_lambda_f(self):
        for _lambda in [10.0, 10000.0]:
            prefix = "basis_f-mp-Lambda" + str(_lambda) + "_np8"
            rb = ir.basis("../irbasis.h5", prefix)
            check_data_ulx = rb._check_ulx()
            for _data in check_data_ulx:
                self.assertLessEqual(_data[2], 1e-8)

            check_data_vly = rb._check_vly()
            for _data in check_data_vly:
                self.assertLessEqual(_data[2], 1e-8)

    def test_small_lambda_b(self):
        for _lambda in [10.0, 10000.0]:
            prefix = "basis_b-mp-Lambda" + str(_lambda) + "_np8"
            rb = ir.basis("../irbasis.h5", prefix)
            check_data_ulx = rb._check_ulx()
            for _data in check_data_ulx:
                self.assertLessEqual(_data[2], 1e-8)

            check_data_vly = rb._check_vly()
            for _data in check_data_vly:
                self.assertLessEqual(_data[2], 1e-8)

    def test_vectorized_ulx(self):
        for _lambda in [10.0]:
            prefix = "basis_b-mp-Lambda" + str(_lambda) + "_np8"
            rb = ir.basis("../irbasis.h5", prefix)

            x = 0.1
            ulx_data = rb.ulx_all_l(x)
            for l in range(rb.dim()):
                self.assertAlmostEqual(ulx_data[l], rb.ulx(l, x), delta=1e-10)

    def test_differential_ulx(self):
        for _lambda in [10.0, 10000.0]:
            prefix = "basis_f-mp-Lambda" + str(_lambda) + "_np8"
            rb_np8 = ir.basis("../irbasis.h5", prefix)
            d_ulx_ref_np8 = rb_np8._get_d_ulx_ref()
            d_ulx_ref_np8_1st = d_ulx_ref_np8[d_ulx_ref_np8[:, 2] == 1][0][3]
            d_ulx_ref_np8_2nd = d_ulx_ref_np8[d_ulx_ref_np8[:, 2] == 2][0][3]
            # 1-st differential
            Nl = rb_np8.dim()
            if Nl % 2 == 1: Nl -= 1
            d_1st_differential = abs((d_ulx_ref_np8_1st - rb_np8.d_ulx(Nl-1, 1.0, 1)) / d_ulx_ref_np8_1st)
            self.assertLessEqual(d_1st_differential, 1e-8)
            # 2-nd differential
            d_2nd_differential = abs((d_ulx_ref_np8_2nd - rb_np8.d_ulx(Nl-1, 1.0, 2)) / d_ulx_ref_np8_2nd)
            self.assertLessEqual(d_2nd_differential, 1e-8)


if __name__ == '__main__':
    unittest.main()

# https://cmake.org/pipermail/cmake/2012-May/050120.html
