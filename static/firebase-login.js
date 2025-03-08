'use strict';

// import firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyCaZWhN23dRlBmFj0suHu0a_Ti7SGQnGfg",
    authDomain: "winged-ray-451723-t5.firebaseapp.com",
    projectId: "winged-ray-451723-t5",
    storageBucket: "winged-ray-451723-t5.firebasestorage.app",
    messagingSenderId: "618606676328",
    appId: "1:618606676328:web:a8fc6871599a35f9576edd"
  };

  // Declare Firebase app and auth globally
let auth;

window.addEventListener("load", function() {
    const app = initializeApp(firebaseConfig);
    auth = getAuth(app); // Assign to global variable
    updateUI(document.cookie);
    console.log("hello world load");

    // Signup of a new user to Firebase
    document.getElementById("sign-up").addEventListener("click", function() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            // User created
            const user = userCredential.user;

            // Get ID token and store in cookie
            user.getIdToken().then((token) => {
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
            });
        })
        .catch((error) => {
            console.log(error.code + " " + error.message);
        });
    });

    // Login user to Firebase
    document.getElementById("login").addEventListener("click", function() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            // User logged in
            const user = userCredential.user;
            console.log("logged in");

            // Get ID token and store in cookie
            user.getIdToken().then((token) => {
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
            });
        })
        .catch((error) => {
            console.log(error.code + " " + error.message);
        });
    });
});

// Sign out from Firebase
document.getElementById("sign-out").addEventListener("click", function() {
    if (!auth) {
        console.error("Firebase Auth is not initialized");
        return;
    }

    signOut(auth)
    .then(() => {
        // Remove ID token and redirect
        document.cookie = "token=;path=/;SameSite=Strict";
        window.location = "/";
    })
    .catch((error) => {
        console.error("Error signing out:", error);
    });
});

// Function to update UI based on authentication status
function updateUI(cookie) {
    var token = parseCookieToken(cookie);

    if (token.length > 0) {
        document.getElementById("login-box").hidden = true;
        document.getElementById("sign-out").hidden = false;
    } else {
        document.getElementById("login-box").hidden = false;
        document.getElementById("sign-out").hidden = true;
    }
}

// Function to parse cookie and get token
function parseCookieToken(cookie) {
    var strings = cookie.split(';');

    for (let i = 0; i < strings.length; i++) {
        var temp = strings[i].trim().split("=");
        if (temp[0] === "token") return temp[1];
    }
    return "";
}
