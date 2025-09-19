"""
Azure DevOps AI Manufacturing MCP - Workflow Management

This module provides intelligent Azure Boards workflow automation for manufacturing
processes, including phase transitions, quality gate validation, and board management.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from .interface import WorkflowManagerInterface
from .types import (
    ManufacturingPhase, TransitionResult, QualityGateResult, QualityGateStatus,
    BoardConfiguration, OperationResult
)


class WorkflowManager(WorkflowManagerInterface):
    """
    Intelligent Azure Boards workflow automation for manufacturing
    
    Maps manufacturing phases to Azure DevOps board column states,
    validates transitions, and manages quality gates.
    """
    
    def __init__(self, manufacturing_phases: Dict[str, str]):
        """
        Initialize workflow manager with phase mapping
        
        Args:
            manufacturing_phases: Dictionary mapping manufacturing phases to Azure DevOps states
        """
        self.phase_mapping = manufacturing_phases
        self.transition_rules = self._initialize_transition_rules()
        self.quality_gates = self._initialize_quality_gates()
        self.board_configurations = {}
        
        # Cache for work item current states
        self._work_item_states = {}
    
    def _initialize_transition_rules(self) -> Dict[str, List[str]]:
        """Initialize valid transition rules between manufacturing phases"""
        return {
            ManufacturingPhase.ANALYSIS.value: [
                ManufacturingPhase.PLANNING.value,
                ManufacturingPhase.CODE_GENERATION.value
            ],
            ManufacturingPhase.PLANNING.value: [
                ManufacturingPhase.CODE_GENERATION.value,
                ManufacturingPhase.ANALYSIS.value  # Allow going back for refinement
            ],
            ManufacturingPhase.CODE_GENERATION.value: [
                ManufacturingPhase.CODE_REVIEW.value,
                ManufacturingPhase.TESTING.value  # Skip review for simple changes
            ],
            ManufacturingPhase.CODE_REVIEW.value: [
                ManufacturingPhase.TESTING.value,
                ManufacturingPhase.CODE_GENERATION.value  # Back to coding if issues found
            ],
            ManufacturingPhase.TESTING.value: [
                ManufacturingPhase.INTEGRATION.value,
                ManufacturingPhase.CODE_GENERATION.value  # Back to coding if tests fail
            ],
            ManufacturingPhase.INTEGRATION.value: [
                ManufacturingPhase.DEPLOYMENT.value,
                ManufacturingPhase.TESTING.value  # Back to testing if integration fails
            ],
            ManufacturingPhase.DEPLOYMENT.value: [
                ManufacturingPhase.COMPLETION.value,
                ManufacturingPhase.INTEGRATION.value  # Back to integration if deployment fails
            ],
            ManufacturingPhase.COMPLETION.value: []  # Terminal state
        }
    
    def _initialize_quality_gates(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quality gate definitions for each manufacturing phase"""
        return {
            ManufacturingPhase.ANALYSIS.value: {
                'requirements_documented': True,
                'acceptance_criteria_defined': True,
                'technical_approach_approved': False  # Optional for analysis phase
            },
            ManufacturingPhase.PLANNING.value: {
                'technical_design_complete': True,
                'effort_estimated': True,
                'dependencies_identified': True
            },
            ManufacturingPhase.CODE_GENERATION.value: {
                'code_generated': True,
                'basic_syntax_check': True,
                'ai_confidence_threshold': 0.7  # Minimum confidence score
            },
            ManufacturingPhase.CODE_REVIEW.value: {
                'peer_review_complete': True,
                'code_standards_compliant': True,
                'security_review_passed': True
            },
            ManufacturingPhase.TESTING.value: {
                'unit_tests_passed': True,
                'code_coverage_threshold': 80,
                'integration_tests_passed': True
            },
            ManufacturingPhase.INTEGRATION.value: {
                'build_successful': True,
                'deployment_package_created': True,
                'integration_tests_passed': True
            },
            ManufacturingPhase.DEPLOYMENT.value: {
                'deployment_successful': True,
                'smoke_tests_passed': True,
                'monitoring_configured': True
            },
            ManufacturingPhase.COMPLETION.value: {
                'user_acceptance_complete': True,
                'documentation_updated': True,
                'knowledge_transfer_complete': False  # Optional
            }
        }
    
    async def execute_phase_transition(self, devops_client: Any, organization: str, project: str,
                                     work_item_id: int, target_phase: ManufacturingPhase, 
                                     context: Dict[str, Any]) -> TransitionResult:
        """
        Execute manufacturing phase transition in Azure Boards
        
        Implementation Steps:
        1. Get current work item state and board position
        2. Determine target board column from phase mapping
        3. Validate board rules and transition permissions
        4. Validate quality gates for phase transition
        5. Execute work item state update to move board column
        6. Update manufacturing metadata in custom fields
        7. Send notifications via Azure DevOps service hooks
        """
        try:
            # Get current work item state
            current_phase = await self._get_current_phase(devops_client, organization, project, work_item_id)
            
            # Validate transition is allowed
            if not self._is_transition_valid(current_phase, target_phase):
                return TransitionResult(
                    success=False,
                    from_phase=current_phase,
                    to_phase=target_phase,
                    work_item_id=work_item_id,
                    board_column_updated=False,
                    message=f"Invalid transition from {current_phase.value} to {target_phase.value}"
                )
            
            # Validate quality gates
            quality_result = await self.validate_quality_gates(work_item_id, target_phase)
            if quality_result.status == QualityGateStatus.FAILED:
                return TransitionResult(
                    success=False,
                    from_phase=current_phase,
                    to_phase=target_phase,
                    work_item_id=work_item_id,
                    board_column_updated=False,
                    message=f"Quality gate validation failed: {quality_result.details}"
                )
            
            # Determine target Azure DevOps state
            target_state = self.phase_mapping.get(target_phase.value)
            if not target_state:
                return TransitionResult(
                    success=False,
                    from_phase=current_phase,
                    to_phase=target_phase,
                    work_item_id=work_item_id,
                    board_column_updated=False,
                    message=f"No Azure DevOps state mapping found for phase {target_phase.value}"
                )
            
            # Execute state transition
            transition_success = await self._update_work_item_state(
                devops_client, organization, project, work_item_id, target_state, target_phase, context
            )
            
            if transition_success:
                # Update cached state
                self._work_item_states[work_item_id] = target_phase
                
                return TransitionResult(
                    success=True,
                    from_phase=current_phase,
                    to_phase=target_phase,
                    work_item_id=work_item_id,
                    board_column_updated=True,
                    message=f"Successfully transitioned from {current_phase.value} to {target_phase.value}"
                )
            else:
                return TransitionResult(
                    success=False,
                    from_phase=current_phase,
                    to_phase=target_phase,
                    work_item_id=work_item_id,
                    board_column_updated=False,
                    message="Failed to update work item state in Azure DevOps"
                )
                
        except Exception as e:
            return TransitionResult(
                success=False,
                from_phase=current_phase if 'current_phase' in locals() else ManufacturingPhase.ANALYSIS,
                to_phase=target_phase,
                work_item_id=work_item_id,
                board_column_updated=False,
                message=f"Error during phase transition: {str(e)}"
            )
    
    async def _get_current_phase(self, devops_client: Any, organization: str, project: str, 
                               work_item_id: int) -> ManufacturingPhase:
        """Get current manufacturing phase from work item"""
        # Check cache first
        if work_item_id in self._work_item_states:
            return self._work_item_states[work_item_id]
        
        # Fetch from Azure DevOps (simplified implementation)
        # In a real implementation, this would call Azure DevOps REST API
        # to get the work item and extract the current phase from custom fields
        
        # For now, return a default phase
        current_phase = ManufacturingPhase.ANALYSIS
        self._work_item_states[work_item_id] = current_phase
        return current_phase
    
    def _is_transition_valid(self, from_phase: ManufacturingPhase, to_phase: ManufacturingPhase) -> bool:
        """Validate if transition between phases is allowed"""
        allowed_transitions = self.transition_rules.get(from_phase.value, [])
        return to_phase.value in allowed_transitions
    
    async def _update_work_item_state(self, devops_client: Any, organization: str, project: str,
                                    work_item_id: int, target_state: str, target_phase: ManufacturingPhase,
                                    context: Dict[str, Any]) -> bool:
        """Update work item state and manufacturing metadata in Azure DevOps"""
        try:
            # Prepare update operations for Azure DevOps PATCH API
            operations = [
                {
                    "op": "replace",
                    "path": "/fields/System.State",
                    "value": target_state
                },
                {
                    "op": "replace",
                    "path": "/fields/Custom.AI.CurrentPhase",
                    "value": target_phase.value
                },
                {
                    "op": "replace",
                    "path": "/fields/Custom.AI.PhaseTransitionTime",
                    "value": datetime.now().isoformat()
                }
            ]
            
            # Add progress percentage if provided in context
            if 'progress_percentage' in context:
                operations.append({
                    "op": "replace",
                    "path": "/fields/Custom.AI.ProgressPercentage",
                    "value": context['progress_percentage']
                })
            
            # Add quality metrics if provided
            if 'quality_metrics' in context:
                operations.append({
                    "op": "replace",
                    "path": "/fields/Custom.AI.QualityMetrics",
                    "value": str(context['quality_metrics'])  # Store as string for simplicity
                })
            
            # Add transition notes if provided
            if 'notes' in context:
                operations.append({
                    "op": "add",
                    "path": "/fields/System.History",
                    "value": f"Phase transition to {target_phase.value}: {context['notes']}"
                })
            
            # In a real implementation, this would make the actual API call to Azure DevOps
            # url = f"https://dev.azure.com/{organization}/{project}/_apis/wit/workitems/{work_item_id}?api-version=6.0"
            # response = await devops_client.patch(url, json=operations)
            # return response.status in [200, 201]
            
            # For now, simulate success
            return True
            
        except Exception as e:
            print(f"Error updating work item state: {str(e)}")
            return False
    
    async def validate_quality_gates(self, work_item_id: int, target_phase: ManufacturingPhase) -> QualityGateResult:
        """
        Validate quality gates before phase transition
        
        Integration with Azure DevOps Quality Gates:
        - Azure Pipelines quality gates for builds
        - Azure Test Plans for test execution validation
        - Azure Artifacts for package quality checks
        - Custom quality rules via Azure DevOps Extensions
        """
        try:
            phase_gates = self.quality_gates.get(target_phase.value, {})
            
            if not phase_gates:
                return QualityGateResult(
                    gate_name=f"{target_phase.value}_quality_gate",
                    status=QualityGateStatus.PASSED,
                    score=1.0,
                    details={"message": "No quality gates defined for this phase"}
                )
            
            # Validate each quality gate requirement
            validation_results = {}
            overall_score = 0.0
            total_gates = len(phase_gates)
            
            for gate_name, requirement in phase_gates.items():
                # Simulate quality gate validation
                # In a real implementation, this would integrate with:
                # - Azure Pipelines for build/test results
                # - Azure Test Plans for test execution
                # - Code analysis tools for quality metrics
                # - Custom validation logic
                
                gate_result = await self._validate_individual_gate(
                    work_item_id, gate_name, requirement, target_phase
                )
                validation_results[gate_name] = gate_result
                
                if gate_result['passed']:
                    overall_score += 1.0
            
            overall_score = overall_score / total_gates if total_gates > 0 else 1.0
            
            # Determine overall status
            if overall_score >= 0.8:  # 80% of gates must pass
                status = QualityGateStatus.PASSED
            elif overall_score >= 0.5:  # 50-80% partial pass (may require manual approval)
                status = QualityGateStatus.PENDING
            else:
                status = QualityGateStatus.FAILED
            
            return QualityGateResult(
                gate_name=f"{target_phase.value}_quality_gate",
                status=status,
                score=overall_score,
                details={
                    "validation_results": validation_results,
                    "gates_passed": int(overall_score * total_gates),
                    "total_gates": total_gates,
                    "threshold": 0.8
                }
            )
            
        except Exception as e:
            return QualityGateResult(
                gate_name=f"{target_phase.value}_quality_gate",
                status=QualityGateStatus.FAILED,
                score=0.0,
                details={"error": str(e)}
            )
    
    async def _validate_individual_gate(self, work_item_id: int, gate_name: str, 
                                      requirement: Any, target_phase: ManufacturingPhase) -> Dict[str, Any]:
        """Validate an individual quality gate requirement"""
        try:
            # Simulate different types of quality gate validations
            if gate_name == 'ai_confidence_threshold':
                # Check AI confidence score from work item metadata
                confidence_score = await self._get_ai_confidence_score(work_item_id)
                passed = confidence_score >= requirement
                return {
                    'passed': passed,
                    'actual_value': confidence_score,
                    'required_value': requirement,
                    'message': f"AI confidence score: {confidence_score} (required: {requirement})"
                }
            
            elif gate_name == 'code_coverage_threshold':
                # Check code coverage from Azure Pipelines
                coverage = await self._get_code_coverage(work_item_id)
                passed = coverage >= requirement
                return {
                    'passed': passed,
                    'actual_value': coverage,
                    'required_value': requirement,
                    'message': f"Code coverage: {coverage}% (required: {requirement}%)"
                }
            
            elif gate_name in ['unit_tests_passed', 'integration_tests_passed', 'build_successful']:
                # Check test/build results from Azure Pipelines
                test_result = await self._get_test_results(work_item_id, gate_name)
                return {
                    'passed': test_result,
                    'actual_value': test_result,
                    'required_value': True,
                    'message': f"{gate_name}: {'PASSED' if test_result else 'FAILED'}"
                }
            
            elif isinstance(requirement, bool):
                # Boolean requirements (like documentation_updated, peer_review_complete)
                actual_value = await self._check_boolean_requirement(work_item_id, gate_name)
                passed = actual_value == requirement
                return {
                    'passed': passed,
                    'actual_value': actual_value,
                    'required_value': requirement,
                    'message': f"{gate_name}: {'COMPLETED' if actual_value else 'PENDING'}"
                }
            
            else:
                # Default validation for unknown gate types
                return {
                    'passed': True,  # Default to pass for unknown gates
                    'actual_value': 'unknown',
                    'required_value': requirement,
                    'message': f"Unknown gate type: {gate_name}"
                }
                
        except Exception as e:
            return {
                'passed': False,
                'actual_value': 'error',
                'required_value': requirement,
                'message': f"Error validating {gate_name}: {str(e)}"
            }
    
    async def _get_ai_confidence_score(self, work_item_id: int) -> float:
        """Get AI confidence score from work item metadata"""
        # In a real implementation, this would fetch from Azure DevOps work item custom fields
        # For now, simulate a confidence score
        return 0.85  # 85% confidence
    
    async def _get_code_coverage(self, work_item_id: int) -> float:
        """Get code coverage from Azure Pipelines build results"""
        # In a real implementation, this would integrate with Azure Pipelines API
        # to get the latest build results and extract code coverage metrics
        return 82.5  # 82.5% coverage
    
    async def _get_test_results(self, work_item_id: int, test_type: str) -> bool:
        """Get test results from Azure Pipelines"""
        # In a real implementation, this would check Azure Pipelines test results
        # For now, simulate test results based on test type
        if test_type == 'unit_tests_passed':
            return True  # Simulate passing unit tests
        elif test_type == 'integration_tests_passed':
            return True  # Simulate passing integration tests
        elif test_type == 'build_successful':
            return True  # Simulate successful build
        else:
            return False
    
    async def _check_boolean_requirement(self, work_item_id: int, requirement_name: str) -> bool:
        """Check boolean requirements like documentation_updated, peer_review_complete"""
        # In a real implementation, this would check various sources:
        # - Azure DevOps work item fields and attachments
        # - Pull request reviews and approvals
        # - Documentation repositories
        # - Manual approval workflows
        
        # For now, simulate different completion states
        completion_simulation = {
            'requirements_documented': True,
            'acceptance_criteria_defined': True,
            'technical_design_complete': True,
            'effort_estimated': True,
            'dependencies_identified': True,
            'code_generated': True,
            'basic_syntax_check': True,
            'peer_review_complete': True,
            'code_standards_compliant': True,
            'security_review_passed': True,
            'deployment_package_created': True,
            'deployment_successful': True,
            'smoke_tests_passed': True,
            'monitoring_configured': False,  # Simulate incomplete monitoring
            'user_acceptance_complete': True,
            'documentation_updated': False,  # Simulate incomplete documentation
            'knowledge_transfer_complete': False
        }
        
        return completion_simulation.get(requirement_name, True)
    
    async def get_board_configuration(self, organization: str, project: str, team: str) -> Dict[str, Any]:
        """
        Retrieve Azure Boards configuration
        
        API Endpoints:
        - GET https://dev.azure.com/{organization}/{project}/{team}/_apis/work/boards
        - GET https://dev.azure.com/{organization}/{project}/{team}/_apis/work/boards/{boardId}/columns
        - GET https://dev.azure.com/{organization}/{project}/{team}/_apis/work/boards/{boardId}/rows
        """
        cache_key = f"{organization}:{project}:{team}"
        
        if cache_key in self.board_configurations:
            return self.board_configurations[cache_key]
        
        # In a real implementation, this would fetch from Azure DevOps API
        # For now, return a simulated board configuration
        board_config = {
            'board_id': f"{team}_board",
            'name': f"{team} Board",
            'columns': [
                {
                    'id': 'new',
                    'name': 'New',
                    'state_mappings': ['New'],
                    'column_type': 'incoming',
                    'item_limit': None
                },
                {
                    'id': 'active',
                    'name': 'Active',
                    'state_mappings': ['Active', 'Approved'],
                    'column_type': 'inProgress',
                    'item_limit': 5
                },
                {
                    'id': 'resolved',
                    'name': 'Resolved',
                    'state_mappings': ['Resolved'],
                    'column_type': 'inProgress',
                    'item_limit': 3
                },
                {
                    'id': 'closed',
                    'name': 'Closed',
                    'state_mappings': ['Closed'],
                    'column_type': 'outgoing',
                    'item_limit': None
                }
            ],
            'swimlanes': [
                {'id': 'default', 'name': 'Stories'},
                {'id': 'expedite', 'name': 'Expedite'}
            ],
            'card_fields': ['System.AssignedTo', 'System.Tags'],
            'card_styles': {}
        }
        
        # Cache the configuration
        self.board_configurations[cache_key] = board_config
        
        return board_config
