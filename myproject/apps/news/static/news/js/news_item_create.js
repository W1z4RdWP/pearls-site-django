document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('id_media_files');
    const fileLabel = document.getElementById('mediaInputLabel');
    const filesList = document.getElementById('mediaFilesList');
    const filesContainer = document.getElementById('mediaFilesContainer');
    const filesCount = document.getElementById('mediaFilesCount');

    if (!fileInput || !fileLabel || !filesList || !filesContainer || !filesCount) {
        return;
    }

    const MAX_FILE_SIZE = 50 * 1024 * 1024;
    const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif'];
    const VIDEO_EXTENSIONS = ['.mp4', '.webm', '.mov', '.avi', '.mkv', '.m4v', '.ogg'];

    let selectedFiles = [];

    function getExtension(fileName) {
        const dotIndex = fileName.lastIndexOf('.');
        return dotIndex === -1 ? '' : fileName.slice(dotIndex).toLowerCase();
    }

    function isImage(file) {
        return file.type.startsWith('image/') || IMAGE_EXTENSIONS.includes(getExtension(file.name));
    }

    function isVideo(file) {
        return file.type.startsWith('video/') || VIDEO_EXTENSIONS.includes(getExtension(file.name));
    }

    function validateFile(file) {
        const errors = [];

        if (file.size > MAX_FILE_SIZE) {
            errors.push('Размер файла превышает 50 МБ');
        }

        if (!isImage(file) && !isVideo(file)) {
            errors.push('Поддерживаются только изображения и видео');
        }

        return errors;
    }

    function formatFileSize(bytes) {
        if (bytes === 0) {
            return '0 Б';
        }

        const units = ['Б', 'КБ', 'МБ', 'ГБ'];
        const power = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
        return `${Math.round((bytes / (1024 ** power)) * 100) / 100} ${units[power]}`;
    }

    function syncFileInput() {
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach((file) => dataTransfer.items.add(file));
        fileInput.files = dataTransfer.files;
    }

    function updateLabel() {
        if (selectedFiles.length === 0) {
            fileLabel.innerHTML = `
                <span class="nfc-file-input-icon" aria-hidden="true">+</span>
                <span>Нажмите для выбора файлов или перетащите их сюда</span>
                <small>Изображения и видео, до 50 МБ на файл</small>
            `;
            return;
        }

        fileLabel.innerHTML = `
            <span class="nfc-file-input-icon" aria-hidden="true">${selectedFiles.length}</span>
            <span>Можно добавить еще файлы</span>
            <small>Порядок сохраняется таким, как вы его выбрали</small>
        `;
    }

    function removeFile(index) {
        selectedFiles.splice(index, 1);
        renderFiles();
    }

    function createFileItem(file, index) {
        const item = document.createElement('div');
        item.className = 'nfc-attachment-item';

        const errors = validateFile(file);
        const preview = document.createElement(isImage(file) ? 'img' : 'div');

        if (isImage(file)) {
            preview.className = 'nfc-attachment-preview';
            preview.alt = file.name;
            const reader = new FileReader();
            reader.onload = function (event) {
                preview.src = event.target.result;
            };
            reader.readAsDataURL(file);
        } else {
            preview.className = 'nfc-attachment-icon';
            preview.textContent = isVideo(file) ? 'VID' : 'FILE';
        }

        const info = document.createElement('div');
        info.className = 'nfc-attachment-info';
        info.innerHTML = `
            <div class="nfc-attachment-name">${file.name}</div>
            <div class="nfc-attachment-meta">${index + 1}. ${isImage(file) ? 'Изображение' : 'Видео'} · ${formatFileSize(file.size)}</div>
            ${errors.length ? `<div class="nfc-attachment-error">${errors.join(', ')}</div>` : ''}
        `;

        const removeButton = document.createElement('button');
        removeButton.type = 'button';
        removeButton.className = 'nfc-attachment-remove';
        removeButton.setAttribute('aria-label', `Удалить ${file.name}`);
        removeButton.textContent = '×';
        removeButton.addEventListener('click', function () {
            removeFile(index);
        });

        item.appendChild(preview);
        item.appendChild(info);
        item.appendChild(removeButton);

        return item;
    }

    function renderFiles() {
        filesContainer.innerHTML = '';
        filesCount.textContent = selectedFiles.length;
        filesList.classList.toggle('has-files', selectedFiles.length > 0);

        selectedFiles.forEach((file, index) => {
            filesContainer.appendChild(createFileItem(file, index));
        });

        updateLabel();
        syncFileInput();
    }

    function addFiles(fileList) {
        let hasRejectedFiles = false;

        Array.from(fileList).forEach((file) => {
            const errors = validateFile(file);
            const duplicate = selectedFiles.some(
                (existingFile) =>
                    existingFile.name === file.name &&
                    existingFile.size === file.size &&
                    existingFile.lastModified === file.lastModified
            );

            if (!errors.length && !duplicate) {
                selectedFiles.push(file);
            } else {
                hasRejectedFiles = true;
            }
        });

        renderFiles();

        if (hasRejectedFiles) {
            window.alert('Часть файлов не была добавлена: проверьте формат, размер или дубли.');
        }
    }

    fileInput.addEventListener('change', function () {
        if (fileInput.files.length) {
            addFiles(fileInput.files);
        }
    });

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
        fileLabel.addEventListener(eventName, function (event) {
            event.preventDefault();
            event.stopPropagation();
        });
    });

    fileLabel.addEventListener('dragover', function () {
        fileLabel.classList.add('is-dragover');
    });

    fileLabel.addEventListener('dragleave', function () {
        fileLabel.classList.remove('is-dragover');
    });

    fileLabel.addEventListener('drop', function (event) {
        fileLabel.classList.remove('is-dragover');
        if (event.dataTransfer.files.length) {
            addFiles(event.dataTransfer.files);
        }
    });
});
