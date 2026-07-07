// ── Element refs ────────────────────────────────────────────
const confSlider  = document.getElementById("conf");
const iouSlider   = document.getElementById("iou");
const confVal     = document.getElementById("confVal");
const iouVal      = document.getElementById("iouVal");
const frameSkipSlider = document.getElementById("frameSkip");
const frameSkipGroup = document.getElementById("frameSkipGroup");
const skipVal     = document.getElementById("skipVal");
const modelSelect = document.getElementById("modelSelect");
const imageSection = document.getElementById("imageMode");
const videoSection = document.getElementById("videoMode");

// Image mode
const imageBtn       = document.getElementById("imageBtn");
const imageInput     = document.getElementById("imageInput");
const imageDropZone  = document.getElementById("imageDropZone");
const annotatedImg   = document.getElementById("annotatedImg");
const imageResultWrap= document.getElementById("imageResultWrap");
const imageTableBody = document.querySelector("#imageTable tbody");

// Video mode
const videoBtn         = document.getElementById("videoBtn");
const videoInput       = document.getElementById("videoInput");
const videoDropZone    = document.getElementById("videoDropZone");
const videoPreviewWrap = document.getElementById("videoPreviewWrap");
const videoPreview     = document.getElementById("videoPreview");
const runVideoBtn      = document.getElementById("runVideoBtn");
const videoResults     = document.getElementById("videoResults");
const videoTableBody   = document.querySelector("#videoTable tbody");

// Spinner
const spinner    = document.getElementById("spinner");
const spinnerMsg = document.getElementById("spinnerMsg");

// ── Slider labels ────────────────────────────────────────────
confSlider.addEventListener("input", () => confVal.textContent = confSlider.value);
iouSlider.addEventListener("input",  () => iouVal.textContent  = iouSlider.value);
frameSkipSlider.addEventListener("input", () => skipVal.textContent = frameSkipSlider.value);

// ── Mode switching ───────────────────────────────────────────
document.querySelectorAll('input[name="mode"]').forEach(radio => {
  radio.addEventListener("change", () => {
    const isImage = radio.value === "image";
    imageSection.hidden = !isImage;
    videoSection.hidden =  isImage;
    frameSkipGroup.hidden = isImage;
  });
});

// ── Helpers ──────────────────────────────────────────────────
function showSpinner(msg = "Running detection…") {
  spinnerMsg.textContent = msg;
  spinner.hidden = false;
}

function hideSpinner() {
  spinner.hidden = true;
}

// The Browse button handles its own click independently.
function setupDragDrop(zone, input) {
  zone.addEventListener("dragover", e => { e.preventDefault(); zone.classList.add("dragover"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
  zone.addEventListener("drop", e => {
    e.preventDefault();
    zone.classList.remove("dragover");
    const file = e.dataTransfer.files[0];
    if (file) {
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      input.dispatchEvent(new Event("change"));
    }
  });
}

// ── IMAGE MODE ───────────────────────────────────────────────
setupDragDrop(imageDropZone, imageInput);

imageBtn.addEventListener("click", () => imageInput.click());

const imagePreviewWrap = document.getElementById("imagePreviewWrap");
const originalImg      = document.getElementById("originalImg");
const runImageBtn      = document.getElementById("runImageBtn");

let currentImageFile = null; // store file so Run button can re-use it

imageInput.addEventListener("change", () => {
  const file = imageInput.files[0];
  if (!file) return;
  imageInput.value = ""; // clear so same file can be re-selected anytime

  currentImageFile = file;
  originalImg.src  = URL.createObjectURL(file);
  imagePreviewWrap.hidden  = false;
  imageResultWrap.hidden   = true;
});

runImageBtn.addEventListener("click", async () => {
  if (!currentImageFile) return;

  runImageBtn.disabled    = true;
  runImageBtn.textContent = "Processing…";
  imageResultWrap.hidden  = true;

  const formData = new FormData();
  formData.append("image", currentImageFile);
  formData.append("conf",  confSlider.value);
  formData.append("iou",   iouSlider.value);
  formData.append("model", modelSelect.value);

  showSpinner("Running detection…");

  try {
    const res = await fetch("/detect/image", { method: "POST", body: formData });

    if (!res.ok) {
      const text = await res.text();
      console.error("Server error:", text);
      alert("Server error " + res.status + ". Check the terminal.");
      return;
    }

    const data = await res.json();
    if (data.error) { alert(data.error); return; }

    annotatedImg.src = "data:image/png;base64," + data.annotated_image;

    imageTableBody.innerHTML = "";
    if (data.detections.length === 0) {
      imageTableBody.innerHTML = `<tr><td colspan="3">No objects detected above threshold.</td></tr>`;
    } else {
      data.detections.forEach((d, i) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${i + 1}</td><td>${d.class}</td><td>${d.confidence}</td>`;
        imageTableBody.appendChild(tr);
      });
    }

    imageResultWrap.hidden = false;
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    hideSpinner();
    runImageBtn.disabled    = false;
    runImageBtn.textContent = "▶️ Run Detection";
  }
});

// ── VIDEO MODE ───────────────────────────────────────────────
setupDragDrop(videoDropZone, videoInput);

videoBtn.addEventListener("click", () => videoInput.click());

let currentVideoFile = null; // store file so Run button can access it after input is cleared

videoInput.addEventListener("change", () => {
  const file = videoInput.files[0];
  if (!file) return;
  videoInput.value = "";        // clear so same file can be re-selected
  currentVideoFile = file;      // keep reference for the run button
  videoPreview.src = URL.createObjectURL(file);
  videoPreviewWrap.hidden = false;
  videoResults.hidden = true;
});

runVideoBtn.addEventListener("click", async () => {
  if (!currentVideoFile) return;  // use stored file, not input.files[0]

  videoResults.hidden = true;
  runVideoBtn.disabled = true;
  runVideoBtn.textContent = "Processing…";

  const formData = new FormData();
  formData.append("video", currentVideoFile);
  formData.append("conf", confSlider.value);
  formData.append("iou", iouSlider.value);
  formData.append("model", modelSelect.value);
  formData.append("frame_skip", frameSkipSlider.value);

  showSpinner("Processing video — this may take a moment…");

  try {
    const res = await fetch("/detect/video", { method: "POST", body: formData });

    if (!res.ok) {
      const text = await res.text();
      console.error("Server error:", text);
      alert("Server error " + res.status + ". Check the terminal.");
      return;
    }

    const data = await res.json();
    if (data.error) { alert(data.error); return; }

    videoTableBody.innerHTML = "";
    if (data.summary.length === 0) {
      videoTableBody.innerHTML = `<tr><td colspan="4">No objects detected above threshold.</td></tr>`;
    } else {
      data.summary.forEach((row, i) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${i + 1}</td><td>${row.class}</td><td>${row.max_in_frame}</td><td>${row.max_conf}</td>`;
        videoTableBody.appendChild(tr);
      });
    }

    videoResults.hidden = false;
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    hideSpinner();
    runVideoBtn.disabled = false;
    runVideoBtn.textContent = "▶️ Run Detection";
  }
});