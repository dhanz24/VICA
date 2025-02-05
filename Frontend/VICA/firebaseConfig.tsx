// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyC_zbFPOc6pzNaBaDhaZr0gP29bTbytJos",
  authDomain: "vica-b11d5.firebaseapp.com",
  databaseURL: "https://vica-b11d5-default-rtdb.asia-southeast1.firebasedatabase.app",
  projectId: "vica-b11d5",
  storageBucket: "vica-b11d5.firebasestorage.app",
  messagingSenderId: "1066307504401",
  appId: "1:1066307504401:web:e5f67a26d4be6b60ac24b0",
  measurementId: "G-CTMFS93WYN"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

export { auth, provider };