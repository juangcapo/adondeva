import { track } from '../api.ts'

/** Mercado Pago payment link. Empty hides the button. */
export const MERCADO_PAGO_URL = 'https://link.mercadopago.com.uy/juangabriel'

export default function Apoyar() {
  return (
    <>
      <h1>Apoyá el sitio</h1>
      <p className="lede">
        ¿A dónde va? es un proyecto independiente, sin publicidad ni financiamiento. Si te sirve, podés colaborar
        para cubrir el servidor, el dominio y las horas de trabajo.
      </p>
      {MERCADO_PAGO_URL ? (
        <p>
          <a className="button" href={MERCADO_PAGO_URL} target="_blank" rel="noopener noreferrer"
            onClick={() => track('evento', 'donar', { datos: {} })}>
            Colaborar con Mercado Pago
          </a>
        </p>
      ) : (
        <p className="muted">Las colaboraciones van a estar disponibles pronto.</p>
      )}
      <p className="muted">
        El pago lo procesa Mercado Pago: podés usar débito, crédito o tu saldo. Este sitio no ve ni guarda tus datos de pago.
      </p>
    </>
  )
}
