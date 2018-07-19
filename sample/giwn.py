from __future__ import print_function
from builtins import range

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

matplotlib.rcParams['font.family'] = 'serif'
matplotlib.rcParams['mathtext.fontset'] = 'cm'
matplotlib.rcParams['mathtext.rm'] = 'serif'

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
        self._x, self._w = _composite_leggauss(12, section_edges)

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
    
    stat = 'F' # 'F' for Fermionic or 'B' for Bosonic
    wmax = 10.0
    Lambda = 1000.0
    beta = Lambda/wmax

    pole = 2.0
    
    assert numpy.abs(pole) <= wmax

    basis = irbasis.load(stat,  Lambda)
    Nl = basis.dim()

    # Initialize a transformer
    trans = transformer(basis, beta)

    # G(tau) generated by a pole at "pole = 2.0"
    if stat == 'B':
        gtau = lambda tau: - pole * numpy.exp(- pole * tau)/(1 - numpy.exp(- beta * pole))
    elif stat == 'F':
        gtau = lambda tau: - numpy.exp(- pole * tau)/(1 + numpy.exp(- beta * pole))
    
    #Compute expansion coefficients in IR by numerical integration
    Gl = trans.compute_gl(gtau, Nl)

    plt.figure(1)
    for l in range(Nl):
        plt.scatter(l,numpy.abs(Gl.real[l]),color = "r")
        
    plt.xlim(1,1e+5)
    plt.ylim(1e-4,1)
 
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel(r'$l$',fontsize = 21)
    plt.tick_params(labelsize=21)
 
    plt.ylabel(r'$|G_l|$',fontsize = 21)
    plt.legend(frameon=False,fontsize = 21)
    plt.tight_layout()
    #plt.show()
    plt.savefig('Gl.png')  
   
    # In this special case, Gl can be computed from rho_l.
    if stat == 'B':
        rhol = pole*numpy.sqrt(1/wmax) * numpy.array([basis.vly(l, pole/wmax) for l in range(Nl)])
        Sl = numpy.sqrt(beta * wmax**3 / 2) * numpy.array([basis.sl(l) for l in range(Nl)])
    elif stat == 'F':
        rhol = numpy.sqrt(1/wmax) * numpy.array([basis.vly(l, pole/wmax) for l in range(Nl)])
        Sl = numpy.sqrt(beta * wmax / 2) * numpy.array([basis.sl(l) for l in range(Nl)])    
    Gl_ref = - Sl * rhol

    # Check Gl is equal to Gl_ref
    numpy.testing.assert_allclose(Gl, Gl_ref, atol=1e-10)

    # Reconstruct G(tau) from Gl
    Nx = 1000
    x_points = numpy.linspace(-1, 1, Nx)
    A = numpy.sqrt(2/beta) * numpy.asarray([basis.ulx(l, x) for x in x_points for l in range(Nl)]).reshape((Nx, Nl))
    Gtau_reconst = numpy.dot(A, Gl)
    Gtau_ref = numpy.asarray([gtau((x+1)*beta/2) for x in x_points])
    numpy.testing.assert_allclose(Gtau_reconst, Gtau_ref, atol=1e-12)

    plt.figure(2)   
    plt.xlim(1,1e+5)
    plt.yscale("log")
    plt.xscale("log")
    
    point = []
    N = 100000
    for x in range(50):
        point.append(int(N * numpy.exp(-x/3.)))
 
    Unl = numpy.sqrt(beta) * basis.compute_unl(point)
    Giw = numpy.dot(Unl, Gl)

    # Compare the result with the exact one 1/(i w_n - pole)
    Glist = []
    reflist = []
    p = 0
    for n in point:
        if stat == 'B':
            wn = (2*n ) * numpy.pi/beta
            ref = pole/(1J * wn - pole)
        elif stat == 'F':
            wn = (2*n +1) * numpy.pi/beta
            ref =  1/(1J * wn - pole)

        Glist.append(numpy.abs(Giw[p]))
        reflist.append(numpy.abs(ref))
        
        # Giw is consistent with ref
        assert numpy.abs(Giw[p] - ref) < 1e-8
        p += 1
       
    
    plt.scatter(point,Glist,marker = "o",label = r"$\rm{Exact} \hspace{0.5}$"+r"$G(i\omega_n)$")
    plt.scatter(point,reflist,marker = "x",label = r"$\rm{Reconstructed\hspace{0.5} from \hspace{0.5}}$"+r"$G_l$")
    plt.tick_params(labelsize=21)
    plt.ylabel(r'$|G(iw_n)|$',fontsize = 21)
    plt.xlabel(r'$n$',fontsize = 21)
    plt.legend(frameon=False,fontsize = 21)
    plt.tight_layout()
    plt.savefig('Giw.png')  
