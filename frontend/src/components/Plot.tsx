import createPlotlyComponent from 'react-plotly.js/factory'
import Plotly from 'plotly.js-dist-min'

// Build the React wrapper from the prebuilt dist bundle instead of the default
// `react-plotly.js` entry (which pulls the full, harder-to-bundle plotly.js).
const Plot = createPlotlyComponent(Plotly)

export default Plot
