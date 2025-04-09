let pdfId = '';
let summaryId = '';

function uploadPDF() {
    const fileInput = document.getElementById('pdf-upload');
    const statusText = document.getElementById('upload-status');
    const file = fileInput.files[0];

    if (!file) {
        statusText.innerHTML = '<span class="status-error">Please select a PDF file.</span>';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    statusText.innerHTML = 'Uploading...';

    fetch('/upload_pdf', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusText.innerHTML = `<span class="status-success">${data.message}</span>`;
            pdfId = data.pdf_id;
            summaryId = data.summary_id;
            document.getElementById('view-pdf-btn').style.display = 'inline-block';
            document.getElementById('view-summary-btn').style.display = 'inline-block';
        } else {
            statusText.innerHTML = `<span class="status-error">${data.message}</span>`;
        }
    })
    .catch(error => {
        statusText.innerHTML = '<span class="status-error">Error uploading file.</span>';
        console.error(error);
    });
}

function viewPDF() {
    if (pdfId) {
        window.open(`/view_pdf/${pdfId}`, '_blank');
    }
}

function viewSummary() {
    if (summaryId) {
        fetch(`/get_summary/${summaryId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const summaryContainer = document.getElementById('summary-container');
                document.getElementById('summary-content').innerText = data.summary;
                summaryContainer.style.display = 'block';
            } else {
                document.getElementById('upload-status').innerHTML = `<span class="status-error">${data.message}</span>`;
            }
        })
        .catch(error => {
            document.getElementById('upload-status').innerHTML = '<span class="status-error">Error retrieving summary.</span>';
            console.error(error);
        });
    }
}