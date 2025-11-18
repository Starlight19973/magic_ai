/**
 * UI interactions для Нейромагии
 * Управление выпадающими меню, модальными окнами и т.д.
 */

// ============================================
// USER PROFILE DROPDOWN
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  const userProfile = document.getElementById('userProfile');
  const userDropdown = document.getElementById('userDropdown');

  if (userProfile && userDropdown) {
    // Toggle dropdown по клику на профиль
    userProfile.addEventListener('click', (e) => {
      e.stopPropagation();
      userProfile.classList.toggle('active');
      userDropdown.classList.toggle('show');
    });

    // Закрытие dropdown при клике вне его области
    document.addEventListener('click', (e) => {
      if (!userProfile.contains(e.target)) {
        userProfile.classList.remove('active');
        userDropdown.classList.remove('show');
      }
    });

    // Закрытие dropdown при нажатии Escape
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        userProfile.classList.remove('active');
        userDropdown.classList.remove('show');
      }
    });
  }
});

// ============================================
// SMOOTH SCROLL для якорных ссылок
// ============================================
document.addEventListener('DOMContentLoaded', () => {
  const smoothScrollLinks = document.querySelectorAll('a[href^="#"]');

  smoothScrollLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      
      // Игнорировать пустые якоря и служебные ссылки
      if (href === '#' || href === '#login' || href === '#signup' || href === '#free') {
        return;
      }

      const target = document.querySelector(href);
      
      if (target) {
        e.preventDefault();
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
});

