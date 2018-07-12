from __future__ import print_function
from builtins import range

import numpy
import irbasis

def _composite_leggauss(deg, section_edges):
    """
    Composite Gauss-Legendre quadrature.

    :param deg: Number of sample points and weights. It must be >= 1.
    :param section_edges: array_like
                          1-D array of the two end points of the integral interval
                          and breaking points in ascending order.
    :return ndarray, ndarray: sampling points and weights
    """
    x_loc, w_loc = numpy.polynomial.legendre.leggauss(deg)

    ns = len(section_edges)-1
    x = numpy.zeros((ns, deg))
    w = numpy.zeros((ns, deg))
    for s in range(ns):
        dx = section_edges[s+1] - section_edges[s]
        x0 = section_edges[s]
        x[s, :] = (dx/2)*(x_loc+1) + x0
        w[s, :] = w_loc*(dx/2)
    return x.reshape((ns*deg)), w.reshape((ns*deg))

class transformer(object):
    def __init__(self, basis, beta):
        section_edges_positive_half = numpy.array(basis.section_edges_x)
        section_edges = numpy.setxor1d(section_edges_positive_half, -section_edges_positive_half)
        self._dim = basis.dim()
        self._beta = beta
        self._x, self._w = _composite_leggauss(16, section_edges)

        nx = len(self._x)
        self._u_smpl = numpy.zeros((nx, self._dim))
        for ix in range(nx):
            self._u_smpl[ix, :] = self._w[ix] * basis.ulx_all_l(self._x[ix])

    def compute_gl(self, gtau, nl):
        assert nl <= self._dim

        nx = len(self._x)
        gtau_smpl = numpy.zeros((1, nx), dtype=complex)
        for ix in range(nx):
            gtau_smpl[0, ix] = gtau(0.5 * (self._x[ix] + 1) * self._beta)

        return numpy.sqrt(self._beta / 2) * numpy.dot(gtau_smpl[:, :], self._u_smpl[:, 0:nl]).reshape((nl))

if __name__ == '__main__':
    beta = 100.0
    Lambda = 1000.0
    wmax = Lambda/beta

    pole = 1.0

    basis = irbasis.load('F',  Lambda)
    Nl = basis.dim()

    # Initialize a transformer
    trans = transformer(basis, beta)

    # G(tau) generated by a pole at "pole"
    gtau = lambda tau: - numpy.exp(- pole * tau)/(1 + numpy.exp(- beta * pole))

    # Compute expansion coefficients in IR by numerical integration
    Gl = trans.compute_gl(gtau, Nl)

    # In this special case, Gl can be computed from rho_l.
    rhol = numpy.sqrt(1/wmax) * numpy.array([basis.vly(l, pole/wmax) for l in range(Nl)])
    Sl = numpy.sqrt(beta * wmax / 2) * numpy.array([basis.sl(l) for l in range(Nl)])
    Gl_ref = - Sl * rhol

    for l in range(Nl):
        print(l, float(Gl[l]), float(Gl_ref[l]))

    # Transform Gl to Matsubara frequency domain
    nvec = numpy.array([0, 10, 100, 1000, 10000, 100000, -10])
    Niw = len(nvec)
    Unl = numpy.sqrt(beta) * basis.compute_unl(nvec)
    Giw = numpy.dot(Unl, Gl)

    # Compare the result with the exact one 1/(i w_n - pole)
    for n in range(Niw):
        wn = (2*nvec[n] + 1) * numpy.pi/beta
        ref = 1/(1J * wn - pole)
        print(nvec[n], numpy.abs((Giw[n] - ref)/ref))
