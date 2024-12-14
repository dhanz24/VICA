import axios from 'axios';
import { auth, provider } from "../../firebaseConfig";
import { signInWithPopup } from "firebase/auth";
import { VICA_BASE_URL } from "../constanta";

const baseService = axios.create({});

const endpoint = VICA_BASE_URL + '/vica/auths';

// interceptor untuk menyisipkan token ke semua request
baseService.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// interceptor untuk menangani token kadaluarsa
baseService.interceptors.response.use(
    (response) => {
        return response;
    },
    (error) => {
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('token'); // Hapus token dari localStorage
            window.location.href = '/login'; // Redirect ke halaman login
        }
        return Promise.reject(error);
    }
);

export const userSignin = async (email : string , password : string) => {
    try {
        const params = {
            email: email,
            password: password,
        };
        const response = await baseService.post(endpoint + '/signin', params);

        if (response.data?.token) {
            localStorage.setItem('token', response.data.token);
        }

        return response.data;
    } catch (error) {
        console.error('Login error:', error);
        throw error;
    }
};

export const userSignup = async (name: string, email: string, password: string, profileImageUrl?: string) => {
    try {
        const params = {
            name: name,
            email: email,
            password: password,
            profile_image_url: profileImageUrl || "",
        };
        const response = await baseService.post(endpoint + '/signup', params);

        if (response.data?.token) {
            localStorage.setItem('token', response.data.token);
        }

        return response.data;
    } catch (error) {
        console.error('Signup error:', error);
        throw error;
    }
};


//FIREBASE AUTH SERVICE
export const loginWithGoogle = async () => {
    try {
      // Sign in dengan Firebase
      const result = await signInWithPopup(auth, provider);
      const user = result.user;
  
      // Dapatkan Firebase ID Token
      const idToken = await user.getIdToken();
    
      const params = {
        id_token: idToken,
      };
      // Kirim ID Token ke backend
      const response = await baseService.post(`${endpoint}/firebase-auth`, params);
  
      if (response.data?.token) {
        localStorage.setItem("token", response.data.token);
      }
  
      return response.data;
    } catch (error) {
      console.error("Google login error:", error);
      throw error;
    }
  };