// styles.js
// Estilos personalizados para react-select.

const customStyles = {
  control: (base, state) => ({
    ...base,
    borderRadius: 4,
    borderColor: state.error ? '#ff0000' : '#000000',
  }),
  input: (base) => ({
    ...base,
    color: '#000000',
  }),
};

export default customStyles;
