const target1 = document.getElementById('typed-text');
const message1 = 'Not getting the Wi-Fi speeds you were promised?';
let index1 = 0;
const typingSpeed = 100; // Speed in milliseconds

// Configuration for second message
const target2 = document.getElementById('typed-text-2');
const message2 = 'We are here to help you keep track of your internet speeds.';
let index2 = 0;


const button = document.querySelector('.btn.btn-primary');

// Function to type out the first message
function typeFirstMessage() {
    if (index1 < message1.length) {
        target1.innerHTML += message1.charAt(index1);
        index1++;
        setTimeout(typeFirstMessage, typingSpeed);
    } else {
        // Start typing the second message after a delay
        setTimeout(typeSecondMessage, 1000);
    }
}

// Function to type out the second message
function typeSecondMessage() {
    if (index2 < message2.length) {
        target2.innerHTML += message2.charAt(index2);
        index2++;
        setTimeout(typeSecondMessage, typingSpeed);
    } else {
        // Show the button once the second message is fully typed
        button.style.display = 'block';
    }
}

// Start typing the first message when the page loads
window.onload = function() {
    typeFirstMessage();
};