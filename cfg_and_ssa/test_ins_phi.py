import unittest
import ast
from Common.cfg_common import ms
from .cfg import Cfg
import A4_CFG.test_helper as th


class TestInsPhi(unittest.TestCase):
    def assertUeVarKill(self, blocks, expected_ue_var, expected_var_kill):
        for block_num in range(len(blocks)):
            self.assertSetEqual(blocks[block_num].ue_var, expected_ue_var[block_num])
            self.assertSetEqual(blocks[block_num].var_kill, expected_var_kill[block_num])

    def assertPhiListEqual(self, block_list, expected_phi_list_dict):
        for block_name, expected_phi_list in expected_phi_list_dict.items():
            real_block = block_list.get_block_by_name(block_name)
            self.assertSetEqual(real_block.phi, expected_phi_list)

    def assertLiveOutEqual(self, block_list, expected_live_out_dict):
        for block_name, expected_live_out_set in expected_live_out_dict.items():
            real_block = block_list.get_block_by_name(block_name)
            self.assertSetEqual(real_block.live_out, expected_live_out_set)

    def test_initial_info_given_3_simple_stmt_expect_ue_a_vk_a_y_x(self):
        as_tree = ast.parse(ms("""\
            a = 3           
            y = a + b         
            x, y = a, b  
            """)
                            )

        cfg_real = Cfg(as_tree)
        cfg_real.gather_initial_info()

        expected_ue_var = {'b'}
        expected_var_kill = {'a', 'y', 'x'}

        self.assertSetEqual(cfg_real.block_list[0].ue_var, expected_ue_var)
        self.assertSetEqual(cfg_real.block_list[0].var_kill, expected_var_kill)

        expected_globals_var = {'b'}
        self.assertSetEqual(cfg_real.globals_var, expected_globals_var)

        expected_block_set = {'x': [cfg_real.block_list[0]], 'a': [cfg_real.block_list[0]],
                              'y': [cfg_real.block_list[0]]}
        self.assertDictEqual(cfg_real.block_set, expected_block_set)

    def test_initial_info_given_3_simple_stmt_given_if(self):
        as_tree = ast.parse(ms("""\
            a = 3    
            if c < 3:       
                y = a + b
                x, y = a, b         
            """)
                            )

        cfg_real = Cfg(as_tree)
        cfg_real.gather_initial_info()

        expected_ue_var = ({'c'}, {'a', 'b'})
        expected_var_kill = ({'a'}, {'y', 'x'})
        self.assertUeVarKill(cfg_real.block_list, expected_ue_var, expected_var_kill)

        expected_globals_var = {'b', 'a', 'c'}
        self.assertSetEqual(cfg_real.globals_var, expected_globals_var)

        expected_block_set = {'x': [cfg_real.block_list[1]], 'a': [cfg_real.block_list[0]],
                              'y': [cfg_real.block_list[1]]}
        self.assertDictEqual(cfg_real.block_set, expected_block_set)

    # ------------------- test phi function insertion-----------------------
    def test_insert_phi_function_semi_pruned(self):
        """
                        Note: '|' with no arrows means pointing down

                         A
                         |
                         B   <------|
                      /    \        |
                     C      F       |
                     |    /  \      |
                     |    G   I     |
                     |    \   /     |
                     |      H       |
                      \    /        |
                        D-----------|
                        |
                        E
                """
        blocks, ast_string = th.build_arbitrary_blocks(block_links={'A': ['B'], 'B': ['C', 'F'], 'C': ['D'],
                                                              'D': ['E', 'B'], 'E': [], 'F': ['G', 'I'],
                                                              'G': ['H'], 'H': ['D'], 'I': ['H']},
                                                       code={'A': ms("""\
                                                            i = 1
                                                            """),
                                                       'B': ms("""\
                                                            a = temp_0
                                                            c = temp_1
                                                            """),
                                                       'C': ms("""\
                                                            b = temp_2
                                                            c = temp_3
                                                            d = temp_4
                                                            """),
                                                       'D': ms("""\
                                                            y = a + b
                                                            z = c + d
                                                            i = i + 1
                                                            if i < 100:
                                                                pass
                                                            """),
                                                       'E': "return\n",
                                                       'F': ms("""\
                                                            a = temp_5
                                                            d = temp_6
                                                            if a < d:
                                                                pass
                                                            """),
                                                       'G': ms("""\
                                                            d = temp
                                                            """),
                                                       'H': ms("""\
                                                            b = temp
                                                            """),
                                                       'I': ms("""\
                                                            c = temp
                                                            """)
                                                       })
        as_tree = ast.parse(ast_string)
        cfg_real = Cfg()
        cfg_real.block_list = blocks
        cfg_real.as_tree = as_tree
        cfg_real.root = cfg_real.block_list[0]
        cfg_real.fill_df()
        cfg_real.gather_initial_info()
        cfg_real.ins_phi_function_semi_pruned()

        expected_phi_list = {'A': set(),
                             'B': {'a', 'b', 'c', 'd', 'i'},
                             'C': set(),
                             'D': {'a', 'b', 'c', 'd'},
                             'E': set(),
                             'F': set(),
                             'G': set(),
                             'H': {'c', 'd'},
                             'I': set()}

        self.assertPhiListEqual(cfg_real.block_list, expected_phi_list)

    def test_insert_phi_function_pruned(self):
        """
                        Note: '|' with no arrows means pointing down

                         A
                         |
                         B   <------|
                      /    \        |
                     C      F       |
                     |    /  \      |
                     |    G   I     |
                     |    \   /     |
                     |      H       |
                      \    /        |
                        D-----------|
                        |
                        E
                """
        blocks, ast_string = th.build_arbitrary_blocks(block_links={'A': ['B'], 'B': ['C', 'F'], 'C': ['D'],
                                                              'D': ['E', 'B'], 'E': [], 'F': ['G', 'I'],
                                                              'G': ['H'], 'H': ['D'], 'I': ['H']},
                                                       code={'A': ms("""\
                                                            i = 1
                                                            """),
                                                       'B': ms("""\
                                                            a = temp_0
                                                            c = temp_1
                                                            if a < c:
                                                                pass
                                                            """),
                                                       'C': ms("""\
                                                            b = temp_2
                                                            c = temp_3
                                                            d = temp_4
                                                            """),
                                                       'D': ms("""\
                                                            y = a + b
                                                            z = c + d
                                                            i = i + 1
                                                            if i < 100:
                                                                pass
                                                            """),
                                                       'E': "return\n",
                                                       'F': ms("""\
                                                            a = temp_5
                                                            d = temp_6
                                                            if a < d:
                                                                pass
                                                            """),
                                                       'G': ms("""\
                                                            d = temp
                                                            """),
                                                       'H': ms("""\
                                                            b = temp
                                                            """),
                                                       'I': ms("""\
                                                            c = temp
                                                            """)
                                                       })
        as_tree = ast.parse(ast_string)
        cfg_real = Cfg()
        cfg_real.block_list = blocks
        cfg_real.as_tree = as_tree
        cfg_real.root = cfg_real.block_list[0]
        cfg_real.fill_df()
        cfg_real.gather_initial_info()
        cfg_real.compute_live_out()
        cfg_real.ins_phi_function_pruned()

        expected_phi_list = {'A': set(),
                             'B': {'i'},
                             'C': set(),
                             'D': {'a', 'b', 'c', 'd'},
                             'E': set(),
                             'F': set(),
                             'G': set(),
                             'H': {'c', 'd'},
                             'I': set()}

        self.assertPhiListEqual(cfg_real.block_list, expected_phi_list)

    def test_insert_phi_function_pruned_4_blocks(self):

        blocks, ast_string = th.build_arbitrary_blocks(block_links={'A': ['B', 'C'], 'B': ['D'], 'C': ['D'], 'D': []},
                                                       code={'A': ms("""\
                                                            pass
                                                            """),
                                                       'B': ms("""\
                                                            var = 3
                                                            """),
                                                       'C': ms("""\
                                                            pass
                                                            """),
                                                       'D': ms("""\
                                                            if var < 3:
                                                                pass
                                                            """)
                                                       })
        as_tree = ast.parse(ast_string)
        cfg_real = Cfg()
        cfg_real.block_list = blocks
        cfg_real.as_tree = as_tree
        cfg_real.root = cfg_real.block_list[0]
        cfg_real.fill_df()
        cfg_real.gather_initial_info()
        cfg_real.compute_live_out()
        cfg_real.ins_phi_function_pruned()

        expected_phi_list = {'A': set(),
                             'B': set(),
                             'C': set(),
                             'D': {'var'}}

        self.assertPhiListEqual(cfg_real.block_list, expected_phi_list)

    # ------------------ test recompute_liveout----------------------------
    def test_recompute_liveout(self):
        # Given: UEVAR(B) = 'c'
        # Expect: LIVEOUT(A) = 'c'
        blocks = th.build_arbitrary_blocks(block_links={'A': ['B'], 'B': []})
        blocks[1].ue_var.add('c')
        self.assertTrue(blocks[0].recompute_liveout())

        self.assertSetEqual(blocks[0].live_out, {'c'})

        # Given: UEVAR(B) = 'c',
        #        LIVEOUT(B) = 'd'
        #        VARKILL(B) = None
        # Expect: LIVEOUT(A) = 'c, 'd'

        blocks = th.build_arbitrary_blocks(block_links={'A': ['B'], 'B': []})
        blocks[1].ue_var.add('c')
        blocks[1].live_out.add('d')
        self.assertTrue(blocks[0].recompute_liveout())

        self.assertSetEqual(blocks[0].live_out, {'c', 'd'})

        # Given: UEVAR(B) = 'c',
        #        LIVEOUT(B) = 'd'
        #        VARKILL(B) = 'd'
        # Expect: LIVEOUT(A) = 'c'

        blocks = th.build_arbitrary_blocks(block_links={'A': ['B'], 'B': []})
        blocks[1].ue_var.add('c')
        blocks[1].live_out.add('d')
        blocks[1].var_kill.add('d')
        self.assertTrue(blocks[0].recompute_liveout())

        self.assertSetEqual(blocks[0].live_out, {'c'})

        # Given: LIVEOUT(A) = 'c'
        #        UEVAR(B) = 'c',
        #        LIVEOUT(B) = 'd'
        #        VARKILL(B) = 'd'
        # Expect: LIVEOUT(A) = 'c' (no changed)

        blocks = th.build_arbitrary_blocks(block_links={'A': ['B'], 'B': []})
        blocks[0].live_out.add('c')
        blocks[1].ue_var.add('c')
        blocks[1].live_out.add('d')
        blocks[1].var_kill.add('d')
        self.assertFalse(blocks[0].recompute_liveout())

        self.assertSetEqual(blocks[0].live_out, {'c'})

    # -------------------- test compute liveout------------------------------
    def test_compute_liveout_given_5_blocks(self):

        blocks, ast_string = th.build_arbitrary_blocks(block_links={'A': ['B'], 'B': ['C', 'D'], 'C': ['D'],
                                                              'D': ['E', 'B'], 'E': []},
                                                       code={'A': ms("""\
                                                                    i = 1
                                                                    """),
                                                       'B': ms("""\
                                                                    if i < 0:
                                                                        pass
                                                                    """),
                                                       'C': ms("""\
                                                                    s = 0
                                                                    """),
                                                       'D': ms("""\
                                                                    s = s + i
                                                                    i = i + 1
                                                                    if i < 0:
                                                                        pass
                                                                    """),
                                                       'E': ms("""\
                                                                    if s < 3:
                                                                        pass
                                                                    """)
                                                       })
        as_tree = ast.parse(ast_string)
        cfg_real = Cfg()
        cfg_real.block_list = blocks
        cfg_real.as_tree = as_tree
        cfg_real.root = cfg_real.block_list[0]
        cfg_real.gather_initial_info()
        cfg_real.compute_live_out()

        expected_live_out = {'A': {'s', 'i'}, 'B': {'s', 'i'}, 'C': {'s', 'i'},
                             'D': {'s', 'i'}, 'E': set()}

        self.assertLiveOutEqual(cfg_real.block_list, expected_live_out)

    # ----------------- functional test phi function insertion--------------
    def test_insert_phi_function(self):
        as_tree = ast.parse(ms("""\
                    a = 3           # 1st
                    if a > 3:       #  |
                        a = 3       # 2nd
                        b = 3
                    else:           # 3rd
                        z = 4       #  |
                    # expected phi func for 'a' here
                    y = a           # 4th
                    """)
                            )
        cfg_real = Cfg(as_tree)
        cfg_real.fill_df()
        cfg_real.gather_initial_info()
        cfg_real.ins_phi_function_semi_pruned()

        expected_phi_list_for_block_3 = {'a'}
        self.assertSetEqual(cfg_real.block_list[-1].phi, expected_phi_list_for_block_3)

        cfg_real.rename_to_ssa()
        pass
