// 投票功能
async function voteForNote(noteId) {
    try {
        const response = await fetch(`/vote/${noteId}`);
        const data = await response.json();

        // 更新票数显示
        const votesElement = document.getElementById(`votes-${noteId}`);
        if (votesElement) {
            votesElement.textContent = data.votes;

            // 添加简单的动画效果
            votesElement.classList.add('text-green-600');
            setTimeout(() => {
                votesElement.classList.remove('text-green-600');
            }, 500);
        }
    } catch (error) {
        console.error('投票失败:', error);
    }
}

// 图片查看器相关变量
let currentNoteImages = [];
let currentImageIndex = 0;

// 打开图片查看器
function openImageViewer(noteId, initialImage) {
    console.log('Opening viewer for note:', noteId, 'initial image:', initialImage); // 调试日志

    // 获取当前笔记的所有图片
    const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
    if (!noteElement) {
        console.error('Note element not found');
        return;
    }

    // 获取所有图片元素并提取src属性
    const images = noteElement.querySelectorAll('img');
    currentNoteImages = Array.from(images).map(img => img.getAttribute('src'));

    console.log('Found images:', currentNoteImages); // 调试日志

    if (currentNoteImages.length === 0) {
        console.error('No images found');
        return;
    }

    currentImageIndex = initialImage || 0;

    // 显示查看器
    const viewer = document.getElementById('imageViewer');
    if (!viewer) {
        console.error('Image viewer element not found');
        return;
    }

    // 设置初始图片
    const fullImage = document.getElementById('fullImage');
    if (fullImage) {
        fullImage.src = currentNoteImages[currentImageIndex];
    }

    // 更新页码
    updatePageNumbers();

    // 显示查看器
    viewer.classList.remove('hidden');

    // 添加键盘事件监听
    document.addEventListener('keydown', handleKeyPress);
}

// 关闭图片查看器
function closeImageViewer() {
    const viewer = document.getElementById('imageViewer');
    if (viewer) {
        viewer.classList.add('hidden');
        document.removeEventListener('keydown', handleKeyPress);
    }
}

// 更新页码显示
function updatePageNumbers() {
    const currentPage = document.getElementById('currentPage');
    const totalPages = document.getElementById('totalPages');

    if (currentPage && totalPages) {
        currentPage.textContent = currentImageIndex + 1;
        totalPages.textContent = currentNoteImages.length;
    }
}

// 切换到上一张图片
function previousImage() {
    if (currentImageIndex > 0) {
        currentImageIndex--;
        const fullImage = document.getElementById('fullImage');
        if (fullImage) {
            fullImage.src = currentNoteImages[currentImageIndex];
            updatePageNumbers();
        }
    }
}

// 切换到下一张图片
function nextImage() {
    if (currentImageIndex < currentNoteImages.length - 1) {
        currentImageIndex++;
        const fullImage = document.getElementById('fullImage');
        if (fullImage) {
            fullImage.src = currentNoteImages[currentImageIndex];
            updatePageNumbers();
        }
    }
}

// 处理键盘事件
function handleKeyPress(e) {
    switch (e.key) {
        case 'ArrowLeft':
            previousImage();
            break;
        case 'ArrowRight':
            nextImage();
            break;
        case 'Escape':
            closeImageViewer();
            break;
    }
}

// 页面加载完成后初始化事件监听
document.addEventListener('DOMContentLoaded', function () {
    console.log('DOM Content Loaded'); // 调试日志

    // 初始化翻页按钮
    const prevButton = document.getElementById('prevImage');
    const nextButton = document.getElementById('nextImage');

    if (prevButton) {
        prevButton.addEventListener('click', function (e) {
            e.preventDefault();
            previousImage();
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', function (e) {
            e.preventDefault();
            nextImage();
        });
    }

    // 点击图片外部区域关闭查看器
    const imageViewer = document.getElementById('imageViewer');
    if (imageViewer) {
        imageViewer.addEventListener('click', function (e) {
            if (e.target === this) {
                closeImageViewer();
            }
        });
    }

    // 确保所有预览按钮都能正常工作
    document.querySelectorAll('button[onclick^="openImageViewer"]').forEach(button => {
        button.addEventListener('click', function (e) {
            e.preventDefault();
            const noteId = this.closest('[data-note-id]').dataset.noteId;
            openImageViewer(noteId, 0);
        });
    });
});

function updateImageViewer() {
    const fullImage = document.getElementById('fullImage');
    if (fullImage && currentNoteImages[currentImageIndex]) {
        // 清除之前的图片
        fullImage.src = '';

        // 创建新图片对象以预加载
        const img = new Image();
        img.onload = function () {
            fullImage.src = this.src;

            // 根据图片比例调整显示
            const container = fullImage.parentElement;
            const containerRatio = container.clientWidth / container.clientHeight;
            const imageRatio = this.width / this.height;

            if (imageRatio > containerRatio) {
                // 图片更宽，使用宽度作为限制
                fullImage.style.width = '100%';
                fullImage.style.height = 'auto';
            } else {
                // 图片更高，使用高度作为限制
                fullImage.style.width = 'auto';
                fullImage.style.height = '100%';
            }
        };
        img.src = currentNoteImages[currentImageIndex];
    }
    updatePageNumbers();
}

// 更新打开查看器的函数
function openImageViewer(noteId, initialImage) {
    const noteElement = document.querySelector(`[data-note-id="${noteId}"]`);
    if (!noteElement) return;

    currentNoteImages = Array.from(noteElement.querySelectorAll('img')).map(img => img.src);
    currentImageIndex = initialImage || 0;

    const viewer = document.getElementById('imageViewer');
    if (viewer) {
        viewer.classList.remove('hidden');
        updateImageViewer();
        document.addEventListener('keydown', handleKeyPress);
    }
}
