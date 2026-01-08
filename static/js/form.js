/**
 * form.js - Manejo del formulario de confirmación de asistencia
 * Incluye validación, envío AJAX y soporte para APP_PREFIX
 */

(function() {
    'use strict';

    // Elementos del DOM
    const form = document.getElementById('confirmacion-form');
    const traeVehiculoSi = document.getElementById('trae_vehiculo_si');
    const traeVehiculoNo = document.getElementById('trae_vehiculo_no');
    const vehiculoFields = document.getElementById('vehiculo_fields');
    const submitBtn = document.getElementById('submitBtn');
    const submitText = document.getElementById('submitText');
    const submitSpinner = document.getElementById('submitSpinner');
    const errorMessage = document.getElementById('error-message');

    // Si este script se carga en una página sin el formulario, salir sin romper.
    if (!form || !traeVehiculoSi || !traeVehiculoNo || !vehiculoFields || !submitBtn || !submitText || !submitSpinner || !errorMessage) {
        return;
    }

    // Inicialización del mapa (Leaflet) si existe el contenedor
    const mapEl = document.getElementById('map');
    if (mapEl && window.L) {
        // 1. Inicialización del mapa con las coordenadas de la FES Aragón
        const map = L.map('map').setView([19.4745, -99.0455], 16);

        // 2. Capa de tiles de OpenStreetMap
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // 3. Marcador: Teatro José Vasconcelos (lugar del evento)
        const teatroCoords = [19.47629921397388, -99.04625437787124];
        const iconUrl = mapEl.getAttribute('data-teatro-icon-url');
        const teatroIcon = iconUrl
            ? L.icon({
                iconUrl,
                iconSize: [40, 40],
                iconAnchor: [20, 40],
                popupAnchor: [0, -36]
            })
            : undefined;

        const markerOptions = teatroIcon ? { icon: teatroIcon } : undefined;
        L.marker(teatroCoords, markerOptions)
            .addTo(map)
            .bindPopup('<strong>Teatro José Vasconcelos</strong><br>FES Aragón')
            .openPopup();

        // Asegurar render correcto si el contenedor se calcula tarde
        setTimeout(() => map.invalidateSize(), 0);
    }

    // Campos de vehículo
    const vehiculoModelo = document.getElementById('vehiculo_modelo');
    const vehiculoColor = document.getElementById('vehiculo_color');
    const vehiculoPlacas = document.getElementById('vehiculo_placas');

    function setVehiculoFieldsVisible(visible) {
        if (visible) {
            vehiculoFields.style.display = 'block';
            vehiculoModelo.required = true;
            vehiculoColor.required = true;
            vehiculoPlacas.required = true;
        } else {
            vehiculoFields.style.display = 'none';
            vehiculoModelo.required = false;
            vehiculoColor.required = false;
            vehiculoPlacas.required = false;
            vehiculoModelo.value = '';
            vehiculoColor.value = '';
            vehiculoPlacas.value = '';
            vehiculoModelo.classList.remove('is-invalid', 'is-valid');
            vehiculoColor.classList.remove('is-invalid', 'is-valid');
            vehiculoPlacas.classList.remove('is-invalid', 'is-valid');
        }
    }

    function getTraeVehiculoValue() {
        const selected = form.querySelector('input[name="trae_vehiculo"]:checked');
        return selected ? selected.value : null;
    }

    // Mostrar/ocultar campos de vehículo según selección Sí/No
    function syncVehiculoFields() {
        const value = getTraeVehiculoValue();
        setVehiculoFieldsVisible(value === 'si');
    }

    traeVehiculoSi.addEventListener('change', syncVehiculoFields);
    traeVehiculoNo.addEventListener('change', syncVehiculoFields);
    syncVehiculoFields();

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

    function getFieldLabel(field) {
        const labels = {
            dependencia: 'Dependencia',
            puesto: 'Puesto',
            grado: 'Grado',
            nombre_completo: 'Nombre completo',
            trae_vehiculo: '¿Asistirá con vehículo?',
            vehiculo_modelo: 'Modelo del vehículo',
            vehiculo_color: 'Color del vehículo',
            vehiculo_placas: 'Placas del vehículo'
        };
        return labels[field] || field;
    }

    function getOrCreateInvalidFeedback(inputEl) {
        if (!inputEl) return null;

        // Radios: mostrar un mensaje para todo el grupo
        if (inputEl.type === 'radio') {
            const group = inputEl.closest('.mb-3');
            if (!group) return null;
            let feedback = group.querySelector('.invalid-feedback[data-for="trae_vehiculo"]');
            if (!feedback) {
                feedback = document.createElement('div');
                feedback.className = 'invalid-feedback d-block';
                feedback.setAttribute('data-for', 'trae_vehiculo');
                group.appendChild(feedback);
            }
            return feedback;
        }

        let feedback = inputEl.parentElement ? inputEl.parentElement.querySelector(`.invalid-feedback[data-for="${inputEl.id}"]`) : null;
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.setAttribute('data-for', inputEl.id || inputEl.name || 'field');
            inputEl.insertAdjacentElement('afterend', feedback);
        }
        return feedback;
    }

    function clearFieldErrors() {
        const all = form.querySelectorAll('input, select, textarea');
        all.forEach(el => {
            el.classList.remove('is-invalid');
            el.setCustomValidity('');
        });
        const feedbackEls = form.querySelectorAll('.invalid-feedback[data-for]');
        feedbackEls.forEach(el => {
            el.textContent = '';
        });
    }

    function showFieldError(field, message) {
        if (!field) {
            showError(message);
            return;
        }

        if (field === 'trae_vehiculo') {
            traeVehiculoSi.classList.add('is-invalid');
            traeVehiculoNo.classList.add('is-invalid');
            const fb = getOrCreateInvalidFeedback(traeVehiculoSi);
            if (fb) fb.textContent = message;
            (fb || traeVehiculoSi).scrollIntoView({ behavior: 'smooth', block: 'center' });
            return;
        }

        const input = document.getElementById(field) || form.querySelector(`[name="${field}"]`);
        if (!input) {
            showError(message);
            return;
        }

        input.classList.add('is-invalid');
        input.setCustomValidity(message);
        const fb = getOrCreateInvalidFeedback(input);
        if (fb) fb.textContent = message;
        input.focus({ preventScroll: true });
        input.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    function friendlyApiMessage(result) {
        if (!result) {
            return { message: 'Por favor verifique los datos ingresados.' };
        }

        const field = result.field;
        const code = result.code;
        const label = field ? getFieldLabel(field) : null;

        if (field && code) {
            if (code === 'required') {
                return { field, message: `Por favor complete: ${label}.` };
            }
            if (code === 'max_length') {
                const max = result.max;
                return { field, message: max ? `${label}: máximo ${max} caracteres.` : `${label}: el texto es demasiado largo.` };
            }
            if (code === 'invalid_choice') {
                return { field, message: `Seleccione una opción válida en: ${label}.` };
            }
            if (code === 'invalid_characters') {
                if (field === 'vehiculo_placas') {
                    return { field, message: 'Placas: use solo letras y números (sin espacios ni guiones).' };
                }
                return { field, message: `${label}: contiene caracteres no permitidos.` };
            }
            if (code === 'invalid') {
                return { field, message: `${label}: valor inválido.` };
            }
        }

        // Fallback: no mostrar el error crudo si podemos “suavizarlo”
        return { field, message: 'Por favor revise los campos marcados y vuelva a intentar.' };
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

        const traeVehiculoValue = getTraeVehiculoValue();

        // Respuesta obligatoria (aunque el required del radio ya cubre esto)
        if (!traeVehiculoValue) {
            isValid = false;
        }

        // Validación adicional de vehículo
        if (traeVehiculoValue === 'si') {
            if (!vehiculoModelo.value.trim()) {
                vehiculoModelo.classList.add('is-invalid');
                const fb = getOrCreateInvalidFeedback(vehiculoModelo);
                if (fb) fb.textContent = 'Por favor indique el modelo del vehículo.';
                isValid = false;
            } else {
                vehiculoModelo.classList.remove('is-invalid');
                vehiculoModelo.classList.add('is-valid');
            }

            if (!vehiculoColor.value.trim()) {
                vehiculoColor.classList.add('is-invalid');
                const fb = getOrCreateInvalidFeedback(vehiculoColor);
                if (fb) fb.textContent = 'Por favor indique el color del vehículo.';
                isValid = false;
            } else {
                vehiculoColor.classList.remove('is-invalid');
                vehiculoColor.classList.add('is-valid');
            }

            if (!vehiculoPlacas.value.trim()) {
                vehiculoPlacas.classList.add('is-invalid');
                const fb = getOrCreateInvalidFeedback(vehiculoPlacas);
                if (fb) fb.textContent = 'Por favor capture las placas del vehículo.';
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
        clearFieldErrors();

        // Validar formulario
        if (!validateForm()) {
            showError('Revise los campos marcados en rojo e intente nuevamente.');
            const firstInvalid = form.querySelector('.is-invalid, :invalid');
            if (firstInvalid && firstInvalid.focus) {
                firstInvalid.focus({ preventScroll: true });
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
            return;
        }

        // Preparar datos
        const formData = new FormData(form);
        const data = {};
        
        formData.forEach((value, key) => {
            data[key] = value;
        });

        // Convertir respuesta Sí/No a boolean (obligatorio)
        const traeVehiculoValue = getTraeVehiculoValue();
        data.trae_vehiculo = traeVehiculoValue === 'si' ? true : (traeVehiculoValue === 'no' ? false : null);

        // Si no trae vehículo, asegurar que los campos están vacíos
        if (data.trae_vehiculo !== true) {
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
                    showError('Ya existe una confirmación registrada con estos datos para este evento. Si cree que es un error, verifique el nombre y la dependencia.');
                } else if (response.status === 400) {
                    // Error de validación
                    const friendly = friendlyApiMessage(result);
                    if (friendly.field) {
                        showFieldError(friendly.field, friendly.message);
                    } else {
                        showError(friendly.message);
                    }
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
                this.setCustomValidity('');
                const fb = getOrCreateInvalidFeedback(this);
                if (fb) fb.textContent = '';
            }
            hideError();
        });
    });

    // Limpiar error del radio al cambiar selección
    traeVehiculoSi.addEventListener('change', function() {
        traeVehiculoSi.classList.remove('is-invalid');
        traeVehiculoNo.classList.remove('is-invalid');
        const fb = getOrCreateInvalidFeedback(traeVehiculoSi);
        if (fb) fb.textContent = '';
        hideError();
    });
    traeVehiculoNo.addEventListener('change', function() {
        traeVehiculoSi.classList.remove('is-invalid');
        traeVehiculoNo.classList.remove('is-invalid');
        const fb = getOrCreateInvalidFeedback(traeVehiculoSi);
        if (fb) fb.textContent = '';
        hideError();
    });

})();
