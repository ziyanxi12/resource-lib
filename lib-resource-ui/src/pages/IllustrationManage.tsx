import { useRef } from 'react'
import IllusList, { type IllusListHandle } from './IllusList'

export default function IllustrationManage() {
  const listRef = useRef<IllusListHandle | null>(null)

  return (
    <IllusList handleRef={listRef} />
  )
}
