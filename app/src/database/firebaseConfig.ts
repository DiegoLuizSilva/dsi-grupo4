// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore/lite";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: process.env.EXPO_PUBLIC_FIREBASE_API_KEY,
  authDomain: "chunguard.firebaseapp.com",
  projectId: "chunguard",
  storageBucket: "chunguard.firebasestorage.app",
  messagingSenderId: "71201998072",
  appId: "1:71201998072:web:06471cbb000705d370670d"
};

// Initialize Firebase
export const app = initializeApp(firebaseConfig);
