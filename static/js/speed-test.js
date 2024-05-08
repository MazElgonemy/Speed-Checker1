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
            var duration = (endTime - startTime) / 50; // Duration in seconds - Should be 1000
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

    document.getElementById('result').textContent = "Calculating speed...";

    // Delay the speed test by 5 seconds
    setTimeout(function() {
        var testFileUrl = '/static/testfile.dat?' + new Date().getTime(); // Cache-busting URL
        downloadFile(testFileUrl, function(duration, fileSize) {
            if (duration && fileSize) {
                var speed = calculateSpeed(duration, fileSize);
                document.getElementById('result').textContent = "Download speed: " + speed + " Mbps";
                sendSpeedToServer(speed);
            } else {
                document.getElementById('result').textContent = "Error performing test";
            }
        });
    }, 8000); // Delays by 8 seconds
});