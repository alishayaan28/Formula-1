'use strict';

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
let registeredUsers = {};

window.addEventListener("load", function() {
    const app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    updateUI(document.cookie);
    console.log("hello world load");

    // Load registered users from localStorage if available (for validation)
    try {
        const storedUsers = localStorage.getItem('registeredUsers');
        if (storedUsers) {
            registeredUsers = JSON.parse(storedUsers);
        }
    } catch (e) {
        console.error("Error loading registered users:", e);
    }

    // Add validation for email and password fields
    const emailInput = document.getElementById("email");
    const passwordInput = document.getElementById("password");
    
    // Add error message for email(@) elements if they don't exist
    if (!document.getElementById("email-error")) {
        const emailErrorDiv = document.createElement("div");
        emailErrorDiv.id = "email-error";
        emailErrorDiv.className = "error-message";
        emailErrorDiv.innerText = "Please enter a valid email with @";
        emailErrorDiv.style.color = "red";
        emailErrorDiv.style.fontSize = "12px";
        emailErrorDiv.style.display = "none";
        emailInput.parentNode.insertBefore(emailErrorDiv, emailInput.nextSibling);
    }
    
    if (!document.getElementById("password-error")) {
        const passwordErrorDiv = document.createElement("div");
        passwordErrorDiv.id = "password-error";
        passwordErrorDiv.className = "error-message";
        passwordErrorDiv.innerText = "Password must be at least 8 characters and include special characters";
        passwordErrorDiv.style.color = "red";
        passwordErrorDiv.style.fontSize = "12px";
        passwordErrorDiv.style.display = "none";
        passwordInput.parentNode.insertBefore(passwordErrorDiv, passwordInput.nextSibling);
    }
    
    if (!document.getElementById("not-registered-error")) {
        const notRegisteredErrorDiv = document.createElement("div");
        notRegisteredErrorDiv.id = "not-registered-error";
        notRegisteredErrorDiv.className = "error-message";
        notRegisteredErrorDiv.innerText = "User not registered. Please sign up first.";
        notRegisteredErrorDiv.style.color = "red";
        notRegisteredErrorDiv.style.fontSize = "12px";
        notRegisteredErrorDiv.style.display = "none";
        document.getElementById("login-box").appendChild(notRegisteredErrorDiv);
    }
    
    // Email validation function
    function validateEmail(email) {
        const emailError = document.getElementById("email-error");
        if (!email.includes('@')) {
            emailError.style.display = 'block';
            return false;
        } else {
            emailError.style.display = 'none';
            return true;
        }
    }
    
    // Password validation function
    function validatePassword(password) {
        const passwordError = document.getElementById("password-error");
        const specialChars = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/;
        
        if (password.length < 8 || !specialChars.test(password)) {
            passwordError.style.display = 'block';
            return false;
        } else {
            passwordError.style.display = 'none';
            return true;
        }
    }
    
    emailInput.addEventListener("input", function() {
        validateEmail(this.value);
    });
    
    passwordInput.addEventListener("input", function() {
        validatePassword(this.value);
    });

    // Signup of a new user to Firebase
    const originalSignUp = document.getElementById("sign-up").onclick;
    document.getElementById("sign-up").onclick = null; // Remove original listener
    
    document.getElementById("sign-up").addEventListener("click", function() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const notRegisteredError = document.getElementById("not-registered-error");
        
        notRegisteredError.style.display = 'none';
        
        const isEmailValid = validateEmail(email);
        const isPasswordValid = validatePassword(password);
        
        if (!isEmailValid || !isPasswordValid) {
            return;
        }

        // Store user in our local validation system
        registeredUsers[email] = true;
        try {
            localStorage.setItem('registeredUsers', JSON.stringify(registeredUsers));
        } catch (e) {
            console.error("Error storing registered users:", e);
        }

        // Proceed with Firebase signup
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
            
            if (error.code === "auth/email-already-in-use") {
                const emailError = document.getElementById("email-error");
                emailError.innerText = "Email is already in use";
                emailError.style.display = 'block';
            }
        });
    });

    // Login user to Firebase
    const originalLogin = document.getElementById("login").onclick;
    document.getElementById("login").onclick = null;
    
    document.getElementById("login").addEventListener("click", function() {
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;
        const notRegisteredError = document.getElementById("not-registered-error");
        
        const isEmailValid = validateEmail(email);
        const isPasswordValid = validatePassword(password);
        
        if (!isEmailValid || !isPasswordValid) {
            return; // Stop if validation fails
        }
        
        // Check if user is registered
        if (!registeredUsers[email]) {
            notRegisteredError.style.display = 'block';
            return; // Stop if user is not registered
        }

        signInWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
            // User logged in
            const user = userCredential.user;
            notRegisteredError.style.display = 'none';
            console.log("logged in");

            // Get ID token and store in cookie
            user.getIdToken().then((token) => {
                document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                window.location = "/";
            });
        })
        .catch((error) => {
            console.log(error.code + " " + error.message);
            
            if (error.code === "auth/user-not-found") {
                notRegisteredError.style.display = 'block';
            } else if (error.code === "auth/wrong-password") {
                const passwordError = document.getElementById("password-error");
                passwordError.innerText = "Incorrect password";
                passwordError.style.display = 'block';
            }
        });
    });
});

// Sign out from Firebase Function
document.getElementById("sign-out").addEventListener("click", function() {
    if (!auth) {
        console.error("Firebase Auth is not initialized");
        return;
    }

    signOut(auth)
    .then(() => {
        document.cookie = "token=;path=/;SameSite=Strict";
        document.getElementById("user-header").hidden = true;
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
        
        let headerBar = document.getElementById("user-header");
        if (!headerBar) {
            headerBar = document.createElement("div");
            headerBar.id = "user-header";
            headerBar.className = "header-bar";
            document.body.insertBefore(headerBar, document.body.firstChild);
            
            const userEmailDisplay = document.createElement("p");
            userEmailDisplay.id = "user-email-display";
            userEmailDisplay.className = "user-email";
            headerBar.appendChild(userEmailDisplay);
            
            headerBar.appendChild(document.getElementById("sign-out"));
        }
        
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            
            const payload = JSON.parse(jsonPayload);
            if (payload.email) {
                document.getElementById("user-email-display").innerText = payload.email;
            }
        } catch (e) {
            console.error("Error displaying user email:", e);
        }
        
        const welcomePage = document.getElementById("welcome-page");
        if (welcomePage) {
            welcomePage.remove();
        }
    } else {
        document.getElementById("login-box").hidden = false;
        
        const headerBar = document.getElementById("user-header");
        if (headerBar) {
            headerBar.hidden = true;
        }
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