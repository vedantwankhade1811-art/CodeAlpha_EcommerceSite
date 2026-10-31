/**
 * CARTZA — Vanilla JavaScript interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Mobile Menu Drawer
  const menuToggle = document.getElementById('mobileMenuToggle');
  const navDrawer = document.getElementById('mobileNavDrawer');
  const navClose = document.getElementById('mobileNavClose');

  if (menuToggle && navDrawer) {
    const openNav = () => {
      navDrawer.classList.add('open');
      document.body.style.overflow = 'hidden';
      menuToggle.setAttribute('aria-expanded', 'true');
    };

    const closeNav = () => {
      navDrawer.classList.remove('open');
      document.body.style.overflow = '';
      menuToggle.setAttribute('aria-expanded', 'false');
    };

    menuToggle.addEventListener('click', () => {
      if (navDrawer.classList.contains('open')) {
        closeNav();
      } else {
        openNav();
      }
    });

    if (navClose) navClose.addEventListener('click', closeNav);

    navDrawer.addEventListener('click', (e) => {
      if (e.target === navDrawer) {
        closeNav();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && navDrawer.classList.contains('open')) {
        closeNav();
      }
    });

    // Close drawer when any navigation link inside is clicked
    navDrawer.querySelectorAll('a').forEach((link) => {
      link.addEventListener('click', closeNav);
    });
  }

  // 2. Search Modal
  const searchBtn = document.getElementById('headerSearchBtn');
  const searchModal = document.getElementById('searchModal');
  const searchClose = document.getElementById('searchModalClose');
  const searchInput = document.getElementById('modalSearchInput');

  if (searchBtn && searchModal) {
    searchBtn.addEventListener('click', () => {
      searchModal.classList.add('active');
      if (searchInput) {
        setTimeout(() => searchInput.focus(), 50);
      }
    });

    const closeSearch = () => {
      searchModal.classList.remove('active');
    };

    if (searchClose) searchClose.addEventListener('click', closeSearch);

    searchModal.addEventListener('click', (e) => {
      if (e.target === searchModal) {
        closeSearch();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && searchModal.classList.contains('active')) {
        closeSearch();
      }
    });
  }

  // 3. Fallback for broken images
  document.querySelectorAll('img').forEach((img) => {
    img.addEventListener('error', function () {
      if (!this.getAttribute('data-has-failed')) {
        this.setAttribute('data-has-failed', 'true');
        this.src = '/static/images/placeholder.svg';
      }
    });
  });

  // 4. Product Detail: Quantity Selector
  const qtyMinus = document.getElementById('qtyMinus');
  const qtyPlus = document.getElementById('qtyPlus');
  const qtyInput = document.getElementById('qtyInput');

  if (qtyMinus && qtyPlus && qtyInput) {
    qtyMinus.addEventListener('click', () => {
      let val = parseInt(qtyInput.value) || 1;
      if (val > 1) {
        qtyInput.value = val - 1;
      }
    });

    qtyPlus.addEventListener('click', () => {
      let val = parseInt(qtyInput.value) || 1;
      let max = parseInt(qtyInput.getAttribute('max')) || 99;
      if (val < max) {
        qtyInput.value = val + 1;
      }
    });

    qtyInput.addEventListener('change', () => {
      let val = parseInt(qtyInput.value) || 1;
      let max = parseInt(qtyInput.getAttribute('max')) || 99;
      if (val < 1) qtyInput.value = 1;
      if (val > max) qtyInput.value = max;
    });
  }

  // 5. Option Chips (Sizes & Colors selection)
  document.querySelectorAll('.option-chip').forEach((chip) => {
    chip.addEventListener('click', function () {
      const parent = this.closest('.option-chips');
      if (parent) {
        parent.querySelectorAll('.option-chip').forEach((c) => c.classList.remove('selected'));
        this.classList.add('selected');
        const inputId = parent.getAttribute('data-input-target');
        if (inputId) {
          const targetInput = document.getElementById(inputId);
          if (targetInput) targetInput.value = this.getAttribute('data-value');
        }
      }
    });
  });

  // 6. Toast Notification System
  function showToast(message, linkUrl, linkText, type = 'success') {
    let container = document.getElementById('toastContainer');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.className = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast-item toast-${type}`;

    let contentHtml = `<div class="toast-content"><span class="toast-message">${message}</span>`;
    if (linkUrl && linkText) {
      contentHtml += ` <a href="${linkUrl}" class="toast-action-link">${linkText}</a>`;
    }
    contentHtml += `</div><button type="button" class="toast-close" aria-label="Close notification">&times;</button>`;
    toast.innerHTML = contentHtml;

    const closeBtn = toast.querySelector('.toast-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        toast.classList.add('toast-hide');
        setTimeout(() => toast.remove(), 250);
      });
    }

    container.appendChild(toast);

    // Auto dismiss after 4 seconds
    setTimeout(() => {
      if (toast.parentElement) {
        toast.classList.add('toast-hide');
        setTimeout(() => toast.remove(), 250);
      }
    }, 4000);
  }

  // 7. Product Detail: Add to Cart & Buy Now Action Handlers
  const purchaseForm = document.getElementById('productPurchaseForm');
  const addToCartBtn = document.getElementById('addToCartBtn');
  const buyNowBtn = document.getElementById('buyNowBtn');
  const buyNowInput = document.getElementById('buyNowInput');

  if (purchaseForm) {
    // Buy Now: sets buy_now=1 and submits directly to redirect to cart/checkout
    if (buyNowBtn) {
      buyNowBtn.addEventListener('click', (e) => {
        if (buyNowInput) buyNowInput.value = '1';
        // Form submits normally via POST redirecting to cart page
      });
    }

    // Add to Cart: seamless asynchronous submission with header badge update & toast
    if (addToCartBtn) {
      addToCartBtn.addEventListener('click', (e) => {
        e.preventDefault();
        if (buyNowInput) buyNowInput.value = '0';

        const originalText = addToCartBtn.innerHTML;
        addToCartBtn.disabled = true;
        addToCartBtn.innerHTML = '<span>Adding to bag...</span>';

        const formData = new FormData(purchaseForm);

        fetch(purchaseForm.action, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: formData,
        })
          .then((res) => {
            if (!res.ok) {
              return res.json().then((errData) => Promise.reject(errData));
            }
            return res.json();
          })
          .then((data) => {
            addToCartBtn.disabled = false;
            if (data.status === 'success') {
              addToCartBtn.innerHTML = '<span>Added to Bag &#10003;</span>';
              setTimeout(() => {
                addToCartBtn.innerHTML = originalText;
              }, 2200);

              // Update all cart badges across page
              const badges = document.querySelectorAll('.cart-badge');
              badges.forEach((b) => {
                b.textContent = data.cart_count;
                b.style.display = data.cart_count > 0 ? 'inline-flex' : 'none';
              });

              showToast(data.message, '/cart/', 'View Bag &rarr;');
            } else {
              addToCartBtn.innerHTML = originalText;
              showToast(data.message || 'Unable to add item to bag.', null, null, 'error');
            }
          })
          .catch((err) => {
            console.warn('AJAX add to cart encountered fallback:', err);
            addToCartBtn.disabled = false;
            addToCartBtn.innerHTML = originalText;
            if (err && err.message) {
              showToast(err.message, null, null, 'error');
            } else {
              // Fallback to normal form submit if fetch had an unhandled issue
              purchaseForm.submit();
            }
          });
      });
    }
  }

  // 8. Wishlist Toggle Handlers (Cards & Detail Page)
  function handleWishlistToggle(btn) {
    const url = btn.getAttribute('data-url');
    if (!url) return;

    // Retrieve CSRF token from page form or cookie
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
      const match = document.cookie.match(/csrftoken=([^;]+)/);
      if (match) csrfToken = match[1];
    }

    fetch(url, {
      method: 'POST',
      headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': csrfToken || '',
      },
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.status === 'success') {
          if (data.is_wishlisted) {
            btn.classList.add('active');
            btn.setAttribute('title', 'Remove from saved items');
          } else {
            btn.classList.remove('active');
            btn.setAttribute('title', 'Save to wishlist');
          }

          // Update all wishlist counter badges across header & drawer
          const wishlistBadges = document.querySelectorAll('.wishlist-badge');
          wishlistBadges.forEach((badge) => {
            badge.textContent = data.wishlist_count;
            badge.style.display = data.wishlist_count > 0 ? 'inline-flex' : 'none';
          });

          showToast(data.message, '/wishlist/', 'View Wishlist &rarr;');
        }
      })
      .catch((err) => {
        console.error('Wishlist toggle error:', err);
      });
  }

  document.addEventListener('click', (e) => {
    const cardWishlistBtn = e.target.closest('.card-wishlist-btn');
    if (cardWishlistBtn) {
      e.preventDefault();
      e.stopPropagation();
      handleWishlistToggle(cardWishlistBtn);
      return;
    }

    const detailWishlistBtn = e.target.closest('#detailWishlistBtn');
    if (detailWishlistBtn) {
      e.preventDefault();
      handleWishlistToggle(detailWishlistBtn);
      return;
    }
  });
});


