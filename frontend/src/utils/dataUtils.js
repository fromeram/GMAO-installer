// src/utils/dataUtils.js

/**
 * Prepara los datos para enviar a la API, convirtiendo valores string a números donde sea necesario
 * @param {Object} data - Datos a procesar
 * @returns {Object} Datos procesados con los tipos adecuados
 */
export const prepareFormData = (data) => {
    const result = { ...data };
    
    // Producto: convertir valores numéricos
    if (result.quantity !== undefined) {
      result.quantity = Number(result.quantity);
    }
    
    if (result.price !== undefined) {
      result.price = Number(result.price);
    }
    
    if (result.supplier_id !== undefined && result.supplier_id !== "" && result.supplier_id !== null) {
      result.supplier_id = Number(result.supplier_id);
    }
    
    return result;
  };