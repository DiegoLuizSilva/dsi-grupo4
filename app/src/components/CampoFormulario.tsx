import React from 'react';
import { StyleSheet, Text, TextInput, TouchableOpacity, View } from 'react-native';

type CampoNumeroProps = {
  rotulo: string;
  ajuda?: string;
  valor: string;
  onChange: (v: string) => void;
  decimal?: boolean;
};

export function CampoNumero({ rotulo, ajuda, valor, onChange, decimal }: CampoNumeroProps) {
  return (
    <View style={estilos.grupo}>
      <Text style={estilos.rotulo}>{rotulo}</Text>
      {ajuda ? <Text style={estilos.ajuda}>{ajuda}</Text> : null}
      <TextInput
        style={estilos.entrada}
        value={valor}
        onChangeText={(t) =>
          onChange(decimal ? t.replace(/[^0-9.,]/g, '') : t.replace(/[^0-9]/g, ''))
        }
        keyboardType={decimal ? 'decimal-pad' : 'number-pad'}
        placeholder="0"
      />
    </View>
  );
}

type CampoTextoProps = {
  rotulo: string;
  valor: string;
  onChange: (v: string) => void;
  placeholder?: string;
};

export function CampoTexto({ rotulo, valor, onChange, placeholder }: CampoTextoProps) {
  return (
    <View style={estilos.grupo}>
      <Text style={estilos.rotulo}>{rotulo}</Text>
      <TextInput
        style={estilos.entrada}
        value={valor}
        onChangeText={onChange}
        placeholder={placeholder}
        autoCapitalize="words"
      />
    </View>
  );
}

type CampoOpcaoProps = {
  rotulo: string;
  ajuda?: string;
  opcoes: { texto: string; valor: any }[];
  valor: any;
  onChange: (v: any) => void;
};

export function CampoOpcao({ rotulo, ajuda, opcoes, valor, onChange }: CampoOpcaoProps) {
  return (
    <View style={estilos.grupo}>
      <Text style={estilos.rotulo}>{rotulo}</Text>
      {ajuda ? <Text style={estilos.ajuda}>{ajuda}</Text> : null}
      <View style={estilos.linhaOpcoes}>
        {opcoes.map((o) => {
          const ativo = o.valor === valor;
          return (
            <TouchableOpacity
              key={String(o.valor)}
              style={[estilos.opcao, ativo && estilos.opcaoAtiva]}
              onPress={() => onChange(o.valor)}
            >
              <Text style={[estilos.opcaoTexto, ativo && estilos.opcaoTextoAtivo]}>{o.texto}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const estilos = StyleSheet.create({
  grupo: { marginBottom: 14 },
  rotulo: { fontSize: 15, fontWeight: '600', marginBottom: 2, color: '#1F2933' },
  ajuda: { fontSize: 12, color: '#7B8794', marginBottom: 6 },
  entrada: {
    borderWidth: 1,
    borderColor: '#CBD2D9',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    backgroundColor: '#fff',
  },
  linhaOpcoes: { flexDirection: 'row', gap: 8, marginTop: 4 },
  opcao: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD2D9',
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  opcaoAtiva: { backgroundColor: '#2E5496', borderColor: '#2E5496' },
  opcaoTexto: { fontSize: 14, color: '#3E4C59', fontWeight: '500' },
  opcaoTextoAtivo: { color: '#fff', fontWeight: 'bold' },
});