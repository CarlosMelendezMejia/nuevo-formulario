/**
 * form.js - Manejo del formulario de confirmación de asistencia
 * Incluye validación, envío AJAX y soporte para APP_PREFIX
 */

(function() {
    'use strict';

    // Elementos del DOM
    const form = document.getElementById('confirmacion-form');
    const traeVehiculoCheckbox = document.getElementById('trae_vehiculo');
    const vehiculoFields = document.getElementById('vehiculo_fields');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const submitSpinner = document.getElementById('submitSpinner');
    const errorMessage = document.getElementById('error-message');

    // Si este script se carga en una página sin el formulario, salir sin romper.
    if (!form || !traeVehiculoCheckbox || !vehiculoFields || !submitBtn || !submitText || !submitSpinner || !errorMessage) {
        return;
    }

    // Campos de vehículo
    const vehiculoModelo = document.getElementById('vehiculo_modelo');
    const vehiculoColor = document.getElementById('vehiculo_color');
    const vehiculoPlacas = document.getElementById('vehiculo_placas');

    /**
     * Mostrar/ocultar campos de vehículo según checkbox
     */
    traeVehiculoCheckbox.addEventListener('change', function() {
        if (this.checked) {
            vehiculoFields.style.display = 'block';
            // Hacer campos requeridos
            vehiculoModelo.required = true;
            vehiculoColor.required = true;
            vehiculoPlacas.required = true;
        } else {
            vehiculoFields.style.display = 'none';
            // Quitar requerido y limpiar valores
            vehiculoModelo.required = false;
            vehiculoColor.required = false;
            vehiculoPlacas.required = false;
            vehiculoModelo.value = '';
            vehiculoColor.value = '';
            vehiculoPlacas.value = '';
            // Remover clases de validación
            vehiculoModelo.classList.remove('is-invalid', 'is-valid');
            vehiculoColor.classList.remove('is-invalid', 'is-valid');
            vehiculoPlacas.classList.remove('is-invalid', 'is-valid');
        }
    });

    /**
     * Convertir placas a mayúsculas mientras se escribe
     */
    vehiculoPlacas.addEventListener('input', function() {
        this.value = this.value.toUpperCase();
    });

    /**
     * Mostrar mensaje de error
     */
    function showError(message) {
        errorMessage.textContent = message;
        errorMessage.style.display = 'block';
        errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    /**
     * Ocultar mensaje de error
     */
    function hideError() {
        errorMessage.style.display = 'none';
        errorMessage.textContent = '';
    }

    /**
     * Habilitar/deshabilitar botón de envío
     */
    function setSubmitLoading(loading) {
        if (loading) {
            submitBtn.disabled = true;
            submitText.style.display = 'none';
            submitSpinner.style.display = 'inline-block';
        } else {
            submitBtn.disabled = false;
            submitText.style.display = 'inline';
            submitSpinner.style.display = 'none';
        }
    }

    /**
     * Validar formulario
     */
    function validateForm() {
        let isValid = true;

        // Validación de Bootstrap
        if (!form.checkValidity()) {
            isValid = false;
            form.classList.add('was-validated');
        }

        // Validación adicional de vehículo
        if (traeVehiculoCheckbox.checked) {
            if (!vehiculoModelo.value.trim()) {
                vehiculoModelo.classList.add('is-invalid');
                isValid = false;
            } else {
                vehiculoModelo.classList.remove('is-invalid');
                vehiculoModelo.classList.add('is-valid');
            }

            if (!vehiculoColor.value.trim()) {
                vehiculoColor.classList.add('is-invalid');
                isValid = false;
            } else {
                vehiculoColor.classList.remove('is-invalid');
                vehiculoColor.classList.add('is-valid');
            }

            if (!vehiculoPlacas.value.trim()) {
                vehiculoPlacas.classList.add('is-invalid');
                isValid = false;
            } else {
                vehiculoPlacas.classList.remove('is-invalid');
                vehiculoPlacas.classList.add('is-valid');
            }
        }

        return isValid;
    }

    /**
     * Enviar formulario via AJAX
     */
    form.addEventListener('submit', async function(event) {
        event.preventDefault();
        event.stopPropagation();

        hideError();

        // Validar formulario
        if (!validateForm()) {
            showError('Por favor complete todos los campos requeridos correctamente.');
            return;
        }

        // Preparar datos
        const formData = new FormData(form);
        const data = {};
        
        formData.forEach((value, key) => {
            data[key] = value;
        });

        // Agregar checkbox de vehículo (FormData no lo incluye si no está checked)
        data.trae_vehiculo = traeVehiculoCheckbox.checked;

        // Si no trae vehículo, asegurar que los campos están vacíos
        if (!data.trae_vehiculo) {
            data.vehiculo_modelo = '';
            data.vehiculo_color = '';
            data.vehiculo_placas = '';
        }

        // Mostrar loading
        setSubmitLoading(true);

        try {
            // Usar window.API_BASE para construir la URL correcta
            const apiUrl = `${window.API_BASE}/api/confirmacion`;
            
            const response = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok && result.ok) {
                // Éxito - redirigir a página de confirmación
                // Usar la URL de redirect del servidor o construir con API_BASE
                const redirectUrl = result.redirect || `${window.API_BASE}/success`;
                window.location.href = redirectUrl;
            } else {
                // Error del servidor
                setSubmitLoading(false);
                
                if (response.status === 409) {
                    // Error de duplicado
                    showError(result.error || 'Ya existe una confirmación registrada con estos datos.');
                } else if (response.status === 400) {
                    // Error de validación
                    showError(result.error || 'Por favor verifique los datos ingresados.');
                } else {
                    // Otro error
                    showError(result.error || 'Ocurrió un error al procesar su confirmación. Por favor intente nuevamente.');
                }
            }
        } catch (error) {
            console.error('Error al enviar formulario:', error);
            setSubmitLoading(false);
            showError('Error de conexión. Por favor verifique su conexión a internet e intente nuevamente.');
        }
    });

    /**
     * Limpiar validación al escribir en campos
     */
    const inputs = form.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                this.classList.remove('is-invalid');
            }
            hideError();
        });
    });

})();
