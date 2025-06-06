function toggleSubcat(header) {
    header.classList.toggle('open');
    const categoryBlock = header.closest('.category-block'); // самый близкий родитель с классом category-block

    if (!categoryBlock) return;

    const subcatList = categoryBlock.querySelector('.subcategory-list');
    const lessonList = categoryBlock.querySelector('.lesson-list');
    const arrow = header.querySelector('.toggle-arrow');

    function toggleDisplay(element) {
        if (!element) return;
        const isVisible = element.style.display === 'block';
        element.style.display = isVisible ? 'none' : 'block';
    }

    toggleDisplay(subcatList);
    toggleDisplay(lessonList);

    if (arrow) {
        const anyOpen = (subcatList && subcatList.style.display === 'block') || (lessonList && lessonList.style.display === 'block');
        arrow.innerHTML = anyOpen ? '&#9660;' : '&#9654;'; // ▼ или ▶
    }
}
