import torch
import torch.fx.experimental.fx_acc.acc_ops as acc_ops
from caffe2.torch.fb.fx2trt.tests.test_utils import AccTestCase
from torch.fx.experimental.fx2trt.passes.fuse_pass import (
    fuse_permute_linear,
    trt_transposed_linear,
)


class TestFusePermuteLinear(AccTestCase):
    def test_fuse_permute_linear(self):
        class TestModule(torch.nn.Module):
            def __init__(self, in_features, out_features):
                super().__init__()
                self.linear = torch.nn.Linear(in_features, out_features)

            def forward(self, x):
                return self.linear(x.permute(0, 2, 1))

        inputs = [torch.randn(6, 10, 20)]
        a = TestModule(10, 30)
        self.run_test(
            TestModule(10, 30),
            inputs,
            {trt_transposed_linear},
            apply_passes=[fuse_permute_linear],
        )

    def test_fuse_permute_linear_keep_permute(self):
        """
        Fusion while keep permute node since permute has more than one consumers
        """

        class TestModule(torch.nn.Module):
            def __init__(self, in_features, out_features):
                super().__init__()
                self.linear = torch.nn.Linear(in_features, out_features)

            def forward(self, x):
                y = x.permute(0, 2, 1)
                return self.linear(y), y

        inputs = [torch.randn(6, 10, 20)]
        a = TestModule(10, 30)
        self.run_test(
            TestModule(10, 30),
            inputs,
            {acc_ops.permute, trt_transposed_linear},
            apply_passes=[fuse_permute_linear],
        )

    def test_multi_fuse_permute_linear(self):
        """
        Fusion when permute output is shared by multiple linears
        """

        class TestModule(torch.nn.Module):
            def __init__(self, in_features, out_features):
                super().__init__()
                self.linear1 = torch.nn.Linear(in_features, out_features)
                self.linear2 = torch.nn.Linear(in_features, out_features)

            def forward(self, x):
                y = x.permute(0, 2, 1)
                return self.linear1(y) + self.linear2(y)

        inputs = [torch.randn(8, 10, 20)]
        a = TestModule(10, 30)
        self.run_test(
            TestModule(10, 30),
            inputs,
            {trt_transposed_linear},
            apply_passes=[fuse_permute_linear],
        )
