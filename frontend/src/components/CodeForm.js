// src/components/CodeForm.js
import React, { useEffect } from 'react';
import { Form, Input, Switch } from 'antd';

const { TextArea } = Input;

// Este componente recibe el formulario de Ant (`form`), los datos iniciales (`initialData`)
// y opcionalmente un flag para incluir el campo active
const CodeForm = ({ form, initialData, includeActive = false }) => {

  // Usamos useEffect para resetear/rellenar el formulario cuando cambian los datos iniciales
  useEffect(() => {
    if (initialData) {
      // Editando: rellenar formulario con datos existentes
      form.setFieldsValue(initialData);
    } else {
      // Añadiendo: limpiar formulario
      form.resetFields();
      
      // Si incluimos el campo active, establecer su valor por defecto a true para nuevos códigos
      if (includeActive) {
        form.setFieldsValue({ active: true });
      }
    }
  }, [initialData, form, includeActive]); // Se ejecuta si initialData, form o includeActive cambian

  return (
    <Form
      form={form}
      layout="vertical"
      name="code_form"
      // initialValues se maneja con setFieldsValue en useEffect para más control
    >
      <Form.Item
        name="code"
        label="Código"
        rules={[
          { required: true, message: 'Por favor, introduzca el código.' },
          { max: 50, message: 'El código no puede exceder los 50 caracteres.' },
        ]}
      >
        <Input />
      </Form.Item>
      <Form.Item
        name="description"
        label="Descripción"
        rules={[
          { required: true, message: 'Por favor, introduzca la descripción.' },
          { max: 255, message: 'La descripción no puede exceder los 255 caracteres.' },
        ]}
      >
        <TextArea rows={3} />
      </Form.Item>
      
      {/* Añadir campo active solo si se solicita */}
      {includeActive && (
        <Form.Item
          name="active"
          label="Estado"
          valuePropName="checked"
        >
          <Switch
            checkedChildren="Activo"
            unCheckedChildren="Inactivo"
          />
        </Form.Item>
      )}
    </Form>
  );
};

export default CodeForm;