// 投票功能实现
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

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function () {
    // PDF文件上传预览
    const pdfInput = document.getElementById('pdf');
    if (pdfInput) {
        pdfInput.addEventListener('change', function (e) {
            const fileName = e.target.files[0]?.name;
            if (fileName) {
                // 更新文件名显示
                const fileLabel = document.querySelector('.pdf-file-label');
                if (fileLabel) {
                    fileLabel.textContent = `已选择: ${fileName}`;
                }
            }
        });
    }

    // 处理闪现消息
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        // 3秒后自动隐藏消息
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 300);
        }, 3000);
    });

    // 图片切换功能
    const noteImages = document.querySelectorAll('.note-images');
    noteImages.forEach(container => {
        const images = container.querySelectorAll('img');
        if (images.length > 1) {
            let currentIndex = 0;

            // 添加切换按钮
            const prevButton = container.querySelector('.prev-button');
            const nextButton = container.querySelector('.next-button');

            if (prevButton && nextButton) {
                prevButton.addEventListener('click', () => {
                    images[currentIndex].classList.add('hidden');
                    currentIndex = (currentIndex - 1 + images.length) % images.length;
                    images[currentIndex].classList.remove('hidden');
                });

                nextButton.addEventListener('click', () => {
                    images[currentIndex].classList.add('hidden');
                    currentIndex = (currentIndex + 1) % images.length;
                    images[currentIndex].classList.remove('hidden');
                });
            }
        }
    });

    // 平滑滚动
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href').slice(1);
            const targetElement = document.getElementById(targetId);

            if (targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // 移动端菜单
    const menuButton = document.querySelector('.mobile-menu-button');
    const mobileMenu = document.querySelector('.mobile-menu');

    if (menuButton && mobileMenu) {
        menuButton.addEventListener('click', () => {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // 表单验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('border-red-500');
                } else {
                    field.classList.remove('border-red-500');
                }
            });

            if (!isValid) {
                e.preventDefault();
            }
        });
    });
});

// 工具函数：防抖
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
} 