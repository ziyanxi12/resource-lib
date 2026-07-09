import { useRef } from 'react'
import ComponentList, { type ComponentListHandle } from './ComponentList'

export default function ComponentManage() {
  const listRef = useRef<ComponentListHandle | null>(null)

  return (
    <ComponentList handleRef={listRef} />
  )
}
