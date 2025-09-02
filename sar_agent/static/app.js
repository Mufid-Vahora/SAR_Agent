async function sendPrompt() {
    const prompt = document.getElementById("prompt").value;
    const responseBox = document.getElementById("llmResponse");
    responseBox.textContent = "Generating...";
    const res = await fetch("/llm/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
    });
    const data = await res.json();
    responseBox.textContent = data.response;
}

async function uploadFile() {
    const fileInput = document.getElementById("fileInput");
    if (!fileInput.files.length) return alert("Select a file first!");
    const formData = new FormData();
    formData.append("file", fileInput.files[0]);

    const res = await fetch("/upload/file", {
        method: "POST",
        body: formData
    });
    const data = await res.json();
    document.getElementById("fileResponse").textContent = JSON.stringify(data, null, 2);
}
