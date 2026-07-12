// Type shims for the Plotly imports that ship without their own types.
// @types/react-plotly.js types the main entry + PlotParams, but not the
// `/factory` subpath, and plotly.js-dist-min has no types.

declare module 'react-plotly.js/factory' {
  import * as React from 'react'
  import { PlotParams } from 'react-plotly.js'
  export default function createPlotlyComponent(
    plotly: unknown,
  ): React.ComponentClass<PlotParams>
}

declare module 'plotly.js-dist-min' {
  const Plotly: unknown
  export default Plotly
}
