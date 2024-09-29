// Open Modal
function openModal(img) {
    var modal = document.getElementById('imageModal');
    var modalImg = document.getElementById('modalImage');
    modal.style.display = 'block';
    modalImg.src = img.src;
}

// Close Modal
function closeModal() {
    var modal = document.getElementById('imageModal');
    modal.style.display = 'none';
}