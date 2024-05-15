function sendSpeedToServer(speed) {
    fetch('/dashboard', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // If you are using sessions or tokens, you need to include the CSRF token here
            // 'X-CSRF-Token': csrfToken
        },
        body: JSON.stringify({ speed: speed })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Success:', data);
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}

function downloadFile(url, callback) {
    var startTime = performance.now();
    var xhr = new XMLHttpRequest();
    xhr.open("GET", url, true);
    xhr.responseType = "blob";

    xhr.onload = function() {
        if (xhr.status === 200) {
            var endTime = performance.now();
            var duration = (endTime - startTime) / 1000; // Duration in seconds
            var fileSize = xhr.getResponseHeader('Content-Length'); // Size in bytes
            callback(duration, fileSize);
        } else {
            callback(null, null);
        }
    };

    xhr.onerror = function() {
        callback(null, null);
    };

    xhr.send();
}

function calculateSpeed(duration, fileSize) {
    var bitsLoaded = fileSize * 8;
    var speedBps = bitsLoaded / duration;
    var speedKbps = (speedBps / 1024).toFixed(2);
    var speedMbps = (speedKbps / 1024).toFixed(2);
    return speedMbps; // Speed in Mbps
}

document.getElementById('startTestBtn').addEventListener('click', function() {
    var resultElement = document.getElementById('result');
    var message = "Calculating speed";
    var dots = "";
    var interval;

    // Function to animate the message
    function animateMessage() {
        resultElement.textContent = message + dots;
        dots = dots.length < 3 ? dots + "." : "";
    }

    // Start the animation
    interval = setInterval(animateMessage, 500);

    var testFileUrl = '/static/testfile.dat?' + new Date().getTime(); // Cache-busting URL
    downloadFile(testFileUrl, function(duration, fileSize) {
        clearInterval(interval); // Stop the animation
        dots = ""; // Reset the dots

        if (duration && fileSize) {
            var speed = calculateSpeed(duration, fileSize);
            resultElement.textContent = "Download speed: " + speed + " Mbps";
            sendSpeedToServer(speed);
        } else {
            resultElement.textContent = "Error performing test";
        }
    });
});