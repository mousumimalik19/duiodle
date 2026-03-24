export const idlFactory = ({ IDL }) => {
  return IDL.Service({
    'getInfo' : IDL.Func(
        [],
        [IDL.Record({ 'tagline' : IDL.Text, 'appName' : IDL.Text })],
        ['query'],
      ),
    'process_doodle' : IDL.Func([IDL.Vec(IDL.Nat8)], [IDL.Text], []),
  });
};
export const init = ({ IDL }) => { return []; };
