
const imageInput = document.getElementById("image");
const uploadText = document.getElementById("uploadText");
const filename = document.getElementById("filename");
const analyzeBtn = document.getElementById("analyzeBtn");
const uploadForm = document.getElementById("uploadForm");
const dropArea = document.getElementById("dropArea");

imageInput.addEventListener("change", function () {

    if (this.files.length) {

        uploadText.textContent = "Image Selected";

        filename.textContent = this.files[0].name;

        dropArea.classList.add("file-dropped");

    }

});

["dragenter","dragover"].forEach(eventName=>{

    dropArea.addEventListener(eventName,function(e){

        e.preventDefault();

        dropArea.classList.add("dragover");

    });

});

["dragleave","drop"].forEach(eventName=>{

    dropArea.addEventListener(eventName,function(e){

        e.preventDefault();

        dropArea.classList.remove("dragover");

    });

});

dropArea.addEventListener("drop", function (e) {

    e.preventDefault();
    e.stopPropagation();

    dropArea.classList.remove("dragover");

    imageInput.files = e.dataTransfer.files;

    const event = new Event("change");
    imageInput.dispatchEvent(event);

});

dropArea.addEventListener("click", function () {
    imageInput.click();
});

const loadingOverlay=document.getElementById("loadingOverlay");

uploadForm.addEventListener("submit",function(){

    analyzeBtn.disabled=true;

    analyzeBtn.textContent="Analyzing...";

   if (loadingOverlay) {
    loadingOverlay.style.display = "flex";
}

});