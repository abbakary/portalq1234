/**
 * Edit Order Details Modal - Standalone JavaScript
 * Handles modal display, scrolling, and responsive behavior
 */

(function() {
  'use strict';

  // Initialize when DOM is ready
  document.addEventListener('DOMContentLoaded', function() {
    initializeEditOrderModal();
  });

  /**
   * Initialize the Edit Order Details Modal
   */
  function initializeEditOrderModal() {
    const editModal = document.getElementById('editOrderDetailsModal');
    
    if (!editModal) {
      console.warn('Edit Order Details Modal not found');
      return;
    }

    // Event: When modal is shown
    editModal.addEventListener('show.bs.modal', function() {
      handleModalShow();
    });

    // Event: When modal is hidden
    editModal.addEventListener('hide.bs.modal', function() {
      handleModalHide();
    });

    // Handle window resize
    window.addEventListener('resize', function() {
      if (editModal.classList.contains('show')) {
        adjustModalHeight();
      }
    });
  }

  /**
   * Handle modal show event
   */
  function handleModalShow() {
    const editModal = document.getElementById('editOrderDetailsModal');
    const modalBody = editModal.querySelector('.modal-body');

    if (modalBody) {
      // Reset inline height constraints
      modalBody.style.maxHeight = '';
      modalBody.style.minHeight = '';

      // Force a reflow to ensure content is rendered
      void editModal.offsetHeight;

      // Adjust height based on content
      adjustModalHeight();

      // Ensure scroll position is at top
      modalBody.scrollTop = 0;
    }

    // Ensure all buttons and form elements are enabled and clickable
    enableAllInteractiveElements(editModal);
  }

  /**
   * Handle modal hide event
   */
  function handleModalHide() {
    const editModal = document.getElementById('editOrderDetailsModal');
    const modalBody = editModal.querySelector('.modal-body');
    
    if (modalBody) {
      // Reset styles
      modalBody.style.maxHeight = '';
      modalBody.style.minHeight = '';
    }
  }

  /**
   * Adjust modal height based on available viewport space
   */
  function adjustModalHeight() {
    const editModal = document.getElementById('editOrderDetailsModal');
    const modalContent = editModal.querySelector('.modal-content');
    const modalHeader = editModal.querySelector('.modal-header');
    const modalFooter = editModal.querySelector('.modal-footer');
    const modalBody = editModal.querySelector('.modal-body');
    
    if (!modalBody || !modalContent) return;

    // Calculate available height
    const viewportHeight = window.innerHeight;
    const headerHeight = modalHeader ? modalHeader.offsetHeight : 60;
    const footerHeight = modalFooter ? modalFooter.offsetHeight : 60;
    const padding = 32; // 16px top + 16px bottom
    
    // Available height for modal body
    const availableHeight = viewportHeight - headerHeight - footerHeight - padding;
    
    // Set max height for modal body only if needed
    if (modalBody.scrollHeight > availableHeight && availableHeight > 200) {
      modalBody.style.maxHeight = availableHeight + 'px';
    }
  }

  /**
   * Make modal visible and handle content display
   */
  window.showEditOrderModal = function() {
    const editModal = document.getElementById('editOrderDetailsModal');
    if (editModal) {
      const bsModal = new bootstrap.Modal(editModal);
      bsModal.show();
    }
  };

  /**
   * Hide the edit order modal
   */
  window.hideEditOrderModal = function() {
    const editModal = document.getElementById('editOrderDetailsModal');
    if (editModal) {
      const bsModal = bootstrap.Modal.getInstance(editModal);
      if (bsModal) {
        bsModal.hide();
      }
    }
  };

  /**
   * Utility function to ensure card content is visible
   */
  window.ensureCardContentVisible = function() {
    const editModal = document.getElementById('editOrderDetailsModal');
    if (!editModal || !editModal.classList.contains('show')) return;

    const cards = editModal.querySelectorAll('.labour-code-card, .service-card');
    cards.forEach(function(card) {
      // Remove any height restrictions from cards
      card.style.minHeight = 'auto';
      card.style.maxHeight = 'none';

      // Make text and icons visible
      const textElements = card.querySelectorAll('*');
      textElements.forEach(function(el) {
        el.style.display = '';
        el.style.visibility = 'visible';
        el.style.opacity = '1';
      });
    });
  };

  /**
   * Enable all interactive elements in the modal
   */
  function enableAllInteractiveElements(modal) {
    if (!modal) return;

    // Enable all buttons
    const buttons = modal.querySelectorAll('button, [role="button"]');
    buttons.forEach(function(btn) {
      btn.disabled = false;
      btn.removeAttribute('disabled');
      btn.style.pointerEvents = 'auto';
      btn.style.cursor = 'pointer';
    });

    // Enable all form elements
    const inputs = modal.querySelectorAll('input, select, textarea');
    inputs.forEach(function(input) {
      input.disabled = false;
      input.removeAttribute('disabled');
      input.style.pointerEvents = 'auto';
      input.style.cursor = 'pointer';
    });

    // Ensure modal dialog and content have proper pointer events
    const modalDialog = modal.querySelector('.modal-dialog');
    const modalContent = modal.querySelector('.modal-content');

    if (modalDialog) {
      modalDialog.style.pointerEvents = 'auto';
    }
    if (modalContent) {
      modalContent.style.pointerEvents = 'auto';
    }
  }

})();
