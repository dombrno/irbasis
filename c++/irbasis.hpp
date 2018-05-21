#pragma once

#include <iostream>
#include <complex>
//#include <cmath>
#include <vector>
#include <set>
#include <assert.h>
#include <memory>
#include <fstream>
#include <numeric>

#include <hdf5.h>

namespace {

  namespace internal {

    // Simple implementation without meta programming...
    template<typename T, int DIM>
    class multi_array {
    public:
      multi_array() : owner_(true), p_data_(new std::vector<T>(0)) {
      }

      multi_array(int N1) : owner_(true), p_data_(new std::vector<T>(N1)) {
        assert(DIM == 1);
        extents_[0] = N1;
      }

      multi_array(int N1, int N2) : owner_(true), p_data_(new std::vector<T>(N1*N2)) {
        assert(DIM == 2);
        extents_[0] = N1;
        extents_[1] = N2;
      }

      multi_array(int N1, int N2, int N3) : owner_(true), p_data_(new std::vector<T>(N1*N2*N3)) {
        assert(DIM == 3);
        extents_[0] = N1;
        extents_[1] = N2;
        extents_[2] = N3;
      }

      multi_array(std::size_t *dims) {
        resize(dims);
      }

      multi_array(const multi_array<T,DIM>& other) : p_data_(NULL) {
          *this = other;
      }

      ~multi_array() {
        if (this->owner_) {
            delete p_data_;
        }
      }

      multi_array<T,DIM>& operator=(const multi_array<T,DIM>& other) {
          this->owner_ = other.owner_;
          for (int i = 0; i < DIM; ++i) {
              this->extents_[i] = other.extents_[i];
          }

          if (this->p_data_ != NULL) {
              delete this->p_data_;
          }

          if (other.owner_) {
              // allocate memoery and copy data
              if (this->p_data_ == NULL) {
                  this->p_data_ = new std::vector<T>();
              }
              *(this->p_data_) = *(other.p_data_);
          } else {
              // point to the same data
              this->p_data_ = other.p_data_;
          }

          return *this;
      }

      std::size_t extent(int i) const {
        assert(i >= 0);
        assert(i < DIM);
        return extents_[i];
      }

      void resize(std::size_t *dims) {
        if (!owner_) {
            throw std::runtime_error("reisze is not permitted for a view");
        }

        std::size_t tot_size = std::accumulate(dims, dims + DIM, 1, std::multiplies<std::size_t>());
        p_data_->resize(tot_size);
        for (int i = 0; i < DIM; ++i) {
          extents_[i] = dims[i];
        }
      }

      /*
      multi_array<T,DIM-1> make_view(std::size_t most_left_index) {
          return SOMETHING;
      }
      */

      std::size_t num_elements() const {
        return p_data_->size();
      }

      bool view() const {
          return !owner_;
      }

      T *origin() {
        return &((*p_data_)[0]);
      }

      T &operator()(int i) {
        assert(DIM == 1);
        int idx = i;
        assert(idx >= 0 && idx < p_data_->size());
        return (*p_data_)[idx];
      }

      const T &operator()(int i) const {
        assert(DIM == 1);
        int idx = i;
        assert(idx >= 0 && idx < p_data_->size());
        return (*p_data_)[idx];
      }

      T &operator()(int i, int j) {
        assert(DIM == 2);
        int idx = extents_[1] * i + j;
        assert(idx >= 0 && idx < p_data_->size());
        return (*p_data_)[idx];
      }

      const T &operator()(int i, int j) const {
        assert(DIM == 2);
        int idx = extents_[1] * i + j;
        assert(idx >= 0 && idx < p_data_->size());
        return (*p_data_)[idx];
      }

      T &operator()(int i, int j, int k) {
        assert(DIM == 3);
        int idx = (i * extents_[1] + j) * extents_[2] + k;
        assert(idx >= 0 && idx < p_data_->size());
        return (*p_data_)[idx];
      }

      const T &operator()(int i, int j, int k) const {
        assert(DIM == 3);
        int idx = (i * extents_[1] + j) * extents_[2] + k;
        assert(idx >= 0 && idx < p_data_->size());
        return (*p_data_)[idx];
      }

    private:
      bool owner_;
      std::vector<T>* p_data_;
      std::size_t extents_[DIM];
    };

    // https://www.physics.ohio-state.edu/~wilkins/computing/HDF/hdf5tutorial/examples/C/h5_rdwt.c
    // https://support.hdfgroup.org/ftp/HDF5/current/src/unpacked/examples/h5_read.c
    // read a double
    inline double hdf5_read_double(hid_t &file, const std::string &name) {
      hid_t dataset = H5Dopen2(file, name.c_str(), H5P_DEFAULT);
      double data;
      H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data);
      H5Dclose(dataset);
      return data;
    }

    // read an int
    inline int hdf5_read_int(hid_t &file, const std::string &name) {
      hid_t dataset = H5Dopen2(file, name.c_str(), H5P_DEFAULT);
      int data;
      H5Dread(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data);
      H5Dclose(dataset);
      return data;
    }

    // read array of double
    template<int DIM>
    void hdf5_read_double_array(hid_t &file, const std::string &name, std::vector <std::size_t> &extents,
                                std::vector<double> &data) {
      hid_t dataset = H5Dopen2(file, name.c_str(), H5P_DEFAULT);
      hid_t space = H5Dget_space(dataset);
      std::vector <hsize_t> dims(DIM);
      int n_dims = H5Sget_simple_extent_dims(space, &dims[0], NULL);
      assert(n_dims == DIM);
      std::size_t tot_size = std::accumulate(dims.begin(), dims.end(), 1, std::multiplies<double>());
      data.resize(tot_size);
      extents.resize(DIM);
      for (int i = 0; i < DIM; ++i) {
        extents[i] = static_cast<std::size_t>(dims[i]);
      }
      H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data[0]);
      H5Dclose(dataset);
    }

    // read double multi_array
    template<int DIM>
    multi_array<double, DIM> load_multi_array(hid_t &file, const std::string &name) {
      hid_t dataset = H5Dopen2(file, name.c_str(), H5P_DEFAULT);
      hid_t space = H5Dget_space(dataset);
      std::vector <hsize_t> dims(DIM);
      int n_dims = H5Sget_simple_extent_dims(space, &dims[0], NULL);
      assert(n_dims == DIM);
      std::size_t tot_size = std::accumulate(dims.begin(), dims.end(), 1, std::multiplies<std::size_t>());
      std::vector <std::size_t> extents(DIM);
      for (int i = 0; i < DIM; ++i) {
        extents[i] = static_cast<std::size_t>(dims[i]);
      }
      multi_array<double, DIM> a;
      a.resize(&extents[0]);
      H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, a.origin());
      std::vector<double> data(tot_size);
      H5Dread(dataset, H5T_NATIVE_DOUBLE, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data[0]);
      multi_array<double, DIM> b = a;
      H5Dclose(dataset);

      return a;
    }

    // read int multi_array
    template<int DIM>
    multi_array<int, DIM> load_multi_iarray(hid_t &file, const std::string &name) {
      hid_t dataset = H5Dopen2(file, name.c_str(), H5P_DEFAULT);
      hid_t space = H5Dget_space(dataset);
      std::vector <hsize_t> dims(DIM);
      int n_dims = H5Sget_simple_extent_dims(space, &dims[0], NULL);
      assert(n_dims == DIM);
      std::size_t tot_size = std::accumulate(dims.begin(), dims.end(), 1, std::multiplies<std::size_t>());
      std::vector <std::size_t> extents(DIM);
      for (int i = 0; i < DIM; ++i) {
        extents[i] = static_cast<std::size_t>(dims[i]);
      }
      multi_array<int, DIM> a;
      a.resize(&extents[0]);
      H5Dread(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, a.origin());
      std::vector<int> data(tot_size);
      H5Dread(dataset, H5T_NATIVE_INT, H5S_ALL, H5S_ALL, H5P_DEFAULT, &data[0]);
      multi_array<int, DIM> b = a;
      H5Dclose(dataset);
      return a;
    }
  }

  struct func {
    internal::multi_array<int, 1> section_edges;
    internal::multi_array<double, 3> data;
    int np;
    int ns;
  };

  struct ref {
    internal::multi_array<double, 2> data;
    internal::multi_array<double, 1> max;
  };

  class basis {
  public:
    basis(
            const std::string &file_name,
            const std::string &prefix = ""
    ) throw(std::runtime_error) {
      hid_t file = H5Fopen(file_name.c_str(), H5F_ACC_RDONLY, H5P_DEFAULT);
      //read info
      Lambda_ = internal::hdf5_read_double(file, prefix + std::string("/info/Lambda"));
      dim_ = internal::hdf5_read_int(file, prefix + std::string("/info/dim"));
      statistics_ = internal::hdf5_read_int(file, prefix + std::string("/info/statistics")) == 0 ? "B" : "F";

      //read sl
      sl_ = internal::load_multi_array<1>(file, prefix + std::string("/sl"));

      //read ulx
      ulx_.data = internal::load_multi_array<3>(file, prefix + std::string("/ulx/data"));
      ulx_.np = internal::hdf5_read_int(file, prefix + std::string("/ulx/np"));
      ulx_.ns = internal::hdf5_read_int(file, prefix + std::string("/ulx/ns"));
      ulx_.section_edges = internal::load_multi_iarray<1>(file, prefix + std::string("/ulx/section_edges"));

      //read ref_ulx
      ref_ulx_.data = internal::load_multi_array<2>(file, prefix + std::string("/ulx/ref/data"));
      ref_ulx_.max = internal::load_multi_array<1>(file, prefix + std::string("/ulx/ref/max"));

      //read vly
      vly_.data = internal::load_multi_array<3>(file, prefix + std::string("/vly/data"));
      vly_.np = internal::hdf5_read_int(file, prefix + std::string("/vly/np"));
      vly_.ns = internal::hdf5_read_int(file, prefix + std::string("/vly/ns"));
      vly_.section_edges = internal::load_multi_iarray<1>(file, prefix + std::string("/vly/section_edges"));

      //read ref_vly
      ref_vly_.data = internal::load_multi_array<2>(file, prefix + std::string("/vly/ref/data"));
      ref_vly_.max = internal::load_multi_array<1>(file, prefix + std::string("/vly/ref/max"));

      H5Fclose(file);
    }

    /**
      * Return number of basis functions
      * @return  number of basis functions
      */
    int dim() const { return dim_; }

    double sl(int l) const throw(std::runtime_error) {
      assert(l >= 0 && l < dim());
      return static_cast<double>(sl_(l));
    }

    double ulx(int l, double x){
      if(x >= 0) return _interpolate(x, get_l_data(l, ulx_.data), ulx_.section_edges);
      else return _interpolate(-x, get_l_data(l, ulx_.data), ulx_.section_edges) * _even_odd_sign(l);
    }

    double vly (int l, double y){
      if(y >= 0) return _interpolate(y, get_l_data(l, vly_.data), vly_.section_edges);
      else return _interpolate(-y, get_l_data(l, vly_.data), vly_.section_edges) * _even_odd_sign(l);

    }

    int num_sections_x(){
      return ulx_.data.extent(1);
    }

    int num_sections_y(){
      return vly_.data.extent(1);
    }


  private:
    double Lambda_;
    int dim_;
    std::string statistics_;
    internal::multi_array<double, 1> sl_;
    func ulx_;
    func vly_;
    ref ref_ulx_;
    ref ref_vly_;

    internal::multi_array<double, 2> get_l_data(int l, const internal::multi_array<double, 3> &_data){
      internal::multi_array<double, 2> a(_data.extent(1), _data.extent(2));
      for (int i=0; i<_data.extent(1); i++){
        for (int j=0; j<_data.extent(2); j++) a(i,j) = _data(l, i, j);
      }
      return a;
    }

    int _even_odd_sign(const int l){
      return (l%2==0 ? 1 : -1);
    }

    double _interpolate(double x, const internal::multi_array<double, 2> &_data, const internal::multi_array<int, 1> &section_edges);


  };

};
