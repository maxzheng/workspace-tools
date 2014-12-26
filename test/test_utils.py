from workspace.utils import split_doc

def test_split_doc():
  """
  Main doc
  for test

  :param type name: Param description
                    on second line.
  :param without_type: No type
  """
  assert split_doc(test_split_doc.__doc__) == (
    '\n  Main doc\n  for test',
    {'name': 'Param description\n                    on second line.',
     'without_type': 'No type'
    }
  )
