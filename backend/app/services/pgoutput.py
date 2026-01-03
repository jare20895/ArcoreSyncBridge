import struct
from typing import Optional, Dict, Any, Tuple

# Basic PgOutput Parser
# Protocol: https://www.postgresql.org/docs/current/protocol-logicalrep-message-formats.html

class PgOutputDecoder:
    def __init__(self):
        self.relations = {} # RelID -> Schema/Table/Cols

    def decode(self, payload: bytes) -> Optional[Dict[str, Any]]:
        msg_type = chr(payload[0])
        data = payload[1:]
        
        if msg_type == 'R': # Relation
            return self._decode_relation(data)
        elif msg_type == 'I': # Insert
            return self._decode_insert(data)
        elif msg_type == 'U': # Update
            return self._decode_update(data)
        elif msg_type == 'D': # Delete
            return self._decode_delete(data)
        elif msg_type == 'B': # Begin
            return {"type": "BEGIN"}
        elif msg_type == 'C': # Commit
            return {"type": "COMMIT"}
        else:
            return {"type": "UNKNOWN", "code": msg_type}

    def _read_int32(self, data, offset) -> Tuple[int, int]:
        val = struct.unpack('>i', data[offset:offset+4])[0]
        return val, offset+4

    def _read_string(self, data, offset) -> Tuple[str, int]:
        end = data.find(b'\0', offset)
        if end == -1:
            raise ValueError("String null terminator not found")
        val = data[offset:end].decode('utf-8')
        return val, end+1

    def _decode_relation(self, data):
        # Byte1('R'), Int32(ID), String(Namespace), String(Name), Int8(ReplicaIdent), Int16(NumCols)
        offset = 0
        rel_id, offset = self._read_int32(data, offset)
        namespace, offset = self._read_string(data, offset)
        name, offset = self._read_string(data, offset)
        replica_identity = chr(data[offset])
        offset += 1
        num_cols = struct.unpack('>h', data[offset:offset+2])[0]
        offset += 2
        
        columns = []
        for _ in range(num_cols):
            # Int8(Flags), String(Name), Int32(DataTypeID), Int32(TypeMod)
            flags = data[offset]
            offset += 1
            col_name, offset = self._read_string(data, offset)
            col_type, offset = self._read_int32(data, offset)
            type_mod, offset = self._read_int32(data, offset)
            columns.append({"name": col_name, "type": col_type, "key": bool(flags & 1)}) # 1 = Part of Key? (Verify flags)

        self.relations[rel_id] = {"schema": namespace, "table": name, "columns": columns}
        return {"type": "RELATION", "id": rel_id, "schema": namespace, "table": name}

    def _decode_tuple(self, data, offset, rel_id) -> Tuple[Dict[str, Any], int]:
        # Int16(NumCols), then 't'(text) or 'n'(null) followed by len/data
        num_cols = struct.unpack('>h', data[offset:offset+2])[0]
        offset += 2
        
        row = {}
        columns = self.relations.get(rel_id, {}).get("columns", [])
        
        for i in range(num_cols):
            col_type = chr(data[offset])
            offset += 1
            
            val = None
            if col_type == 'n': # Null
                pass
            elif col_type == 't': # Text
                length, offset = self._read_int32(data, offset)
                val_bytes = data[offset:offset+length]
                val = val_bytes.decode('utf-8')
                offset += length
            elif col_type == 'u': # Unchanged TOAST
                pass 
                
            if i < len(columns):
                row[columns[i]["name"]] = val
            else:
                row[f"col_{i}"] = val
                
        return row, offset

    def _decode_insert(self, data):
        # Byte1('I'), Int32(RelID), Tuple('N')
        offset = 0
        rel_id, offset = self._read_int32(data, offset)
        tuple_type = chr(data[offset]) # 'N'
        offset += 1
        
        row, offset = self._decode_tuple(data, offset, rel_id)
        
        relation = self.relations.get(rel_id, {})
        return {
            "type": "INSERT",
            "schema": relation.get("schema"),
            "table": relation.get("table"),
            "data": row
        }

    def _decode_update(self, data):
        # Byte1('U'), Int32(RelID), Optional OldTuple('K'|'O'), NewTuple('N')
        offset = 0
        rel_id, offset = self._read_int32(data, offset)
        sub_type = chr(data[offset])
        offset += 1
        
        old_row = None
        if sub_type in ('K', 'O'):
            old_row, offset = self._decode_tuple(data, offset, rel_id)
            sub_type = chr(data[offset]) # Read next, should be 'N'
            offset += 1
            
        row, offset = self._decode_tuple(data, offset, rel_id)
        
        relation = self.relations.get(rel_id, {})
        return {
            "type": "UPDATE",
            "schema": relation.get("schema"),
            "table": relation.get("table"),
            "data": row,
            "old_data": old_row
        }

    def _decode_delete(self, data):
        # Byte1('D'), Int32(RelID), OldTuple('K'|'O')
        offset = 0
        rel_id, offset = self._read_int32(data, offset)
        sub_type = chr(data[offset])
        offset += 1
        
        row, offset = self._decode_tuple(data, offset, rel_id)
        
        relation = self.relations.get(rel_id, {})
        return {
            "type": "DELETE",
            "schema": relation.get("schema"),
            "table": relation.get("table"),
            "data": row
        }
