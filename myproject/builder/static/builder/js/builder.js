function toggleSubcat(header) {
    header.classList.toggle('open');
    const subcatList = header.parentElement.querySelector('.subcategory-list');
    const arrow = header.querySelector('.toggle-arrow');
    if (subcatList) {
        const isOpen = subcatList.style.display === 'block';
        subcatList.style.display = isOpen ? 'none' : 'block';
        if (arrow) {
            arrow.innerHTML = isOpen ? '&#9654;' : '&#9660;'; // ▶ ▼
        }
    }
}
