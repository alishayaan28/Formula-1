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
    
    if (emailInput && passwordInput) {
        if (!document.getElementById("global-error-message")) {
            const errorMessageDiv = document.createElement("div");
            errorMessageDiv.id = "global-error-message";
            errorMessageDiv.style.color = "red";
            errorMessageDiv.style.fontWeight = "bold";
            errorMessageDiv.style.padding = "10px";
            errorMessageDiv.style.margin = "10px 0";
            errorMessageDiv.style.display = "none";
            errorMessageDiv.style.backgroundColor = "#ffebee";
            errorMessageDiv.style.borderRadius = "4px";
            errorMessageDiv.style.textAlign = "center";
            
            const loginBox = document.getElementById("login-box");
            if (loginBox) {
                loginBox.insertBefore(errorMessageDiv, loginBox.firstChild);
            }
        }
        
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
        
        const loginBox = document.getElementById("login-box");
        if (loginBox && !document.getElementById("not-registered-error")) {
            const notRegisteredErrorDiv = document.createElement("div");
            notRegisteredErrorDiv.id = "not-registered-error";
            notRegisteredErrorDiv.className = "error-message";
            notRegisteredErrorDiv.innerText = "User not registered. Please sign up first.";
            notRegisteredErrorDiv.style.color = "red";
            notRegisteredErrorDiv.style.fontSize = "12px";
            notRegisteredErrorDiv.style.display = "none";
            loginBox.appendChild(notRegisteredErrorDiv);
        }
        
        // Email validation function
        function validateEmail(email) {
            const emailError = document.getElementById("email-error");
            if (!email.includes('@')) {
                if (emailError) emailError.style.display = 'block';
                return false;
            } else {
                if (emailError) emailError.style.display = 'none';
                return true;
            }
        }
        
        // Password validation function
        function validatePassword(password) {
            const passwordError = document.getElementById("password-error");
            const specialChars = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/;
            
            if (password.length < 8 || !specialChars.test(password)) {
                if (passwordError) passwordError.style.display = 'block';
                return false;
            } else {
                if (passwordError) passwordError.style.display = 'none';
                return true;
            }
        }

        function showGlobalError(message) {
            const errorDiv = document.getElementById("global-error-message");
            if (errorDiv) {
                errorDiv.textContent = message;
                errorDiv.style.display = "block";
            }
        }

        function hideGlobalError() {
            const errorDiv = document.getElementById("global-error-message");
            if (errorDiv) {
                errorDiv.style.display = "none";
            }
        }
        
        emailInput.addEventListener("input", function() {
            const errorDiv = document.getElementById("global-error-message");
            if (errorDiv) errorDiv.style.display = 'none';
            
            const signUpButton = document.getElementById("sign-up");
            if (signUpButton && signUpButton === document.activeElement) {
                validateEmail(this.value);
            }
        });
        
        passwordInput.addEventListener("input", function() {
            const errorDiv = document.getElementById("global-error-message");
            if (errorDiv) errorDiv.style.display = 'none';
            
            const signUpButton = document.getElementById("sign-up");
            if (signUpButton && signUpButton === document.activeElement) {
                validatePassword(this.value);
            }
        });

        // Signup of a new user to Firebase
        const signUpButton = document.getElementById("sign-up");
        if (signUpButton) {
            const originalSignUp = signUpButton.onclick;
            signUpButton.onclick = null;
            
            signUpButton.addEventListener("click", function() {
                const email = document.getElementById("email").value;
                const password = document.getElementById("password").value;
                
                hideGlobalError();
                
                const isEmailValid = validateEmail(email);
                const isPasswordValid = validatePassword(password);
                
                if (!isEmailValid || !isPasswordValid) {
                    return;
                }

                registeredUsers[email] = true;
                try {
                    localStorage.setItem('registeredUsers', JSON.stringify(registeredUsers));
                } catch (e) {
                    console.error("Error storing registered users:", e);
                }

                createUserWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    const user = userCredential.user;

                    user.getIdToken().then((token) => {
                        document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                        window.location = "/";
                    });
                })
                .catch((error) => {
                    console.log(error.code + " " + error.message);
                    
                    if (error.code === "auth/email-already-in-use") {
                        showGlobalError("Email is already in use");
                    } else {
                        showGlobalError("Signup error: " + error.message);
                    }
                });
            });
        }

        // Login user to Firebase
        const loginButton = document.getElementById("login");
        if (loginButton) {
            const originalLogin = loginButton.onclick;
            loginButton.onclick = null;
            
            loginButton.addEventListener("click", function() {
                const email = document.getElementById("email").value;
                const password = document.getElementById("password").value;
                
            
                hideGlobalError();
                
                if (!email) {
                    showGlobalError("Please enter your email");
                    return;
                }
                
                if (!password) {
                    showGlobalError("Please enter your password");
                    return;
                }

                signInWithEmailAndPassword(auth, email, password)
                .then((userCredential) => {
                    // User logged in
                    const user = userCredential.user;
                    console.log("logged in");

                    user.getIdToken().then((token) => {
                        document.cookie = "token=" + token + ";path=/;SameSite=Strict";
                        window.location = "/";
                    });
                })
                .catch((error) => {
                    console.log("Login error:", error.code, error.message);
                    
                    if (error.code === "auth/user-not-found") {
                        showGlobalError("User not found. Please check your email or sign up.");
                    } else if (error.code === "auth/wrong-password") {
                        showGlobalError("Incorrect password. Please try again.");
                    } else if (error.code === "auth/invalid-email") {
                        showGlobalError("Invalid email format. Please try again.");
                    } else if (error.code === "auth/too-many-requests") {
                        showGlobalError("Too many failed login attempts. Please try again later.");
                    } else {
                        showGlobalError("Login failed: " + error.message);
                    }
                });
            });
        }
    }
});

// Sign out from Firebase Function
const signOutButton = document.getElementById("sign-out");
if (signOutButton) {
    signOutButton.addEventListener("click", function() {
        if (!auth) {
            console.error("Firebase Auth is not initialized");
            return;
        }

        signOut(auth)
        .then(() => {
            document.cookie = "token=;path=/;SameSite=Strict";
            const userHeader = document.getElementById("user-header");
            if (userHeader) userHeader.hidden = true;
            window.location = "/";
        })
        .catch((error) => {
            console.error("Error signing out:", error);
        });
    });
}

// Function to update UI based on authentication status
function updateUI(cookie) {
    var token = parseCookieToken(cookie);

    if (token.length > 0) {
        const loginBox = document.getElementById("login-box");
        if (loginBox) {
            loginBox.hidden = true;
        }
        
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
            
            const signOutButton = document.getElementById("sign-out");
            if (signOutButton) {
                headerBar.appendChild(signOutButton);
            }
        }
        
        try {
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
                return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
            }).join(''));
            
            const payload = JSON.parse(jsonPayload);
            const userEmailDisplay = document.getElementById("user-email-display");
            if (payload.email && userEmailDisplay) {
                userEmailDisplay.innerText = payload.email;
            }
        } catch (e) {
            console.error("Error displaying user email:", e);
        }
        
        const welcomePage = document.getElementById("welcome-page");
        if (welcomePage) {
            welcomePage.remove();
        }
    } else {
        const loginBox = document.getElementById("login-box");
        if (loginBox) {
            loginBox.hidden = false;
        }
        
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