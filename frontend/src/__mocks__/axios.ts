const mockAxios: any = {
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  create: jest.fn(() => {
    return mockAxios;
  }),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() }
  }
};

export default mockAxios;