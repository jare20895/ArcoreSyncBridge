import '@testing-library/jest-dom'
import React from 'react'

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: any) {
    return React.createElement(
      'a',
      { href: typeof href === 'string' ? href : href?.pathname || '#', ...props },
      children,
    )
  }
})
