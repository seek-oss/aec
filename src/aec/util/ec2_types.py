from __future__ import annotations

from typing import TYPE_CHECKING, List, Sequence

if TYPE_CHECKING:
    from mypy_boto3_ec2.literals import InstanceTypeType, ShutdownBehaviorType
    from mypy_boto3_ec2.type_defs import (
        BlockDeviceMappingTypeDef,
        CapacityReservationSpecificationTypeDef,
        CpuOptionsRequestTypeDef,
        CreditSpecificationRequestTypeDef,
        ElasticGpuSpecificationTypeDef,
        ElasticInferenceAcceleratorTypeDef,
        EnclaveOptionsRequestTypeDef,
        FilterTypeDef,
        HibernationOptionsRequestTypeDef,
        IamInstanceProfileSpecificationTypeDef,
        InstanceIpv6AddressTypeDef,
        InstanceMarketOptionsRequestTypeDef,
        InstanceMetadataOptionsRequestTypeDef,
        InstanceNetworkInterfaceSpecificationTypeDef,
        LaunchTemplateSpecificationTypeDef,
        LicenseConfigurationRequestTypeDef,
        PlacementTypeDef,
        RunInstancesMonitoringEnabledTypeDef,
        TagSpecificationTypeDef,
    )

from typing_extensions import TypedDict


class _RequiredRunArgs(TypedDict, total=True):
    MaxCount: int
    MinCount: int


class RunArgs(_RequiredRunArgs, total=False):
    BlockDeviceMappings: List["BlockDeviceMappingTypeDef"]
    ImageId: str
    InstanceType: InstanceTypeType
    Ipv6AddressCount: int
    Ipv6Addresses: List["InstanceIpv6AddressTypeDef"]
    KernelId: str
    KeyName: str
    Monitoring: "RunInstancesMonitoringEnabledTypeDef"
    Placement: "PlacementTypeDef"
    RamdiskId: str
    SecurityGroupIds: List[str]
    SecurityGroups: List[str]
    SubnetId: str
    UserData: str
    AdditionalInfo: str
    ClientToken: str
    DisableApiTermination: bool
    DryRun: bool
    EbsOptimized: bool
    IamInstanceProfile: "IamInstanceProfileSpecificationTypeDef"
    InstanceInitiatedShutdownBehavior: ShutdownBehaviorType
    NetworkInterfaces: List["InstanceNetworkInterfaceSpecificationTypeDef"]
    PrivateIpAddress: str
    ElasticGpuSpecification: List["ElasticGpuSpecificationTypeDef"]
    ElasticInferenceAccelerators: List[ElasticInferenceAcceleratorTypeDef]
    TagSpecifications: List["TagSpecificationTypeDef"]
    LaunchTemplate: LaunchTemplateSpecificationTypeDef
    InstanceMarketOptions: InstanceMarketOptionsRequestTypeDef
    CreditSpecification: "CreditSpecificationRequestTypeDef"
    CpuOptions: CpuOptionsRequestTypeDef
    CapacityReservationSpecification: CapacityReservationSpecificationTypeDef
    HibernationOptions: HibernationOptionsRequestTypeDef
    LicenseSpecifications: List[LicenseConfigurationRequestTypeDef]
    MetadataOptions: InstanceMetadataOptionsRequestTypeDef
    EnclaveOptions: EnclaveOptionsRequestTypeDef


class DescribeArgs(TypedDict, total=False):
    Filters: Sequence["FilterTypeDef"]
    InstanceIds: Sequence[str]
    DryRun: bool
    MaxResults: int
    NextToken: str
