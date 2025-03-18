// main.js - Frontend JavaScript for handling PDF uploads and summaries

document.addEventListener("DOMContentLoaded", function() {
    const uploadForm = document.getElementById("upload-form");
    const fileInput = document.getElementById("pdf-upload");
    const uploadStatus = document.getElementById("upload-status");
    const summaryContainer = document.getElementById("summary-container");
    const summaryContent = document.getElementById("summary-content");
    const viewPdfBtn = document.getElementById("view-pdf-btn");
    const viewSummaryBtn = document.getElementById("view-summary-btn");
    const downloadSummaryBtn = document.getElementById("download-summary-btn");
    
    // Global variables to store IDs
    let currentPdfId = null;
    let currentSummaryId = null;
    
    function uploadPDF() {
        let fileInput = document.getElementById("pdf-upload");
        let file = fileInput.files[0];
        let statusText = document.getElementById("upload-status");
    
        if (!file) {
            statusText.innerText = "Please select a PDF file.";
            return;
        }
    
        let formData = new FormData();
        formData.append("file", file);
    
        fetch("http://127.0.0.1:5000/upload_pdf", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                sessionStorage.setItem("summary_id", data.summary_id);
                document.getElementById("view-summary-btn").style.display = "block";
                statusText.innerText = "PDF uploaded successfully! Click 'View Summary'.";
            } else {
                statusText.innerText = data.message;
            }
        })
        .catch(error => {
            statusText.innerText = "Error: " + error.message;
        });
    }
    
    function viewSummary() {
        let summaryID = sessionStorage.getItem("summary_id");
        if (!summaryID) {
            alert("No summary available.");
            return;
        }
    
        fetch(`http://127.0.0.1:5000/get_summary/${summaryID}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById("summary-content").innerText = data.summary;
                document.getElementById("summary").style.display = "block";
            } else {
                alert("Error retrieving summary: " + data.message);
            }
        })
        .catch(error => {
            alert("Error fetching summary: " + error.message);
        });
    }
    
    
    // Add event listeners
    document.getElementById("upload-btn").addEventListener("click", uploadPDF);
    viewSummaryBtn.addEventListener("click", viewSummary);
    viewPdfBtn.addEventListener("click", viewPDF);
    downloadSummaryBtn.addEventListener("click", downloadSummary);
});